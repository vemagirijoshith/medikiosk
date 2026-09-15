"""Read-only assembly of existing D1/C/B5/B6 source data for D3."""
from typing import Any

from sqlalchemy.orm import Session

from app.models import Allergy, Consultation, Document, Encounter, Medication, OCRResult, Patient, Symptom
from app.schemas.medical_extraction import MedicalExtraction
from app.services.ayush_coding_service import map_ayush_codes
from app.services.document_intelligence_service import build_document_intelligence


def _extraction(document: Document, result: OCRResult | None) -> MedicalExtraction | None:
    data = (result.structured_data or {}).get("medical_extraction") if result else None
    if not data:
        return None
    try:
        return MedicalExtraction.model_validate(data)
    except ValueError:
        # A malformed historic extraction is not transformed or supplemented.
        return None


def build_physician_review_packet(db: Session, patient: Patient, encounter_id: int | None) -> dict[str, Any]:
    encounter = (db.query(Encounter).filter(Encounter.id == encounter_id, Encounter.patient_id == patient.id).first()
                 if encounter_id is not None else
                 db.query(Encounter).filter(Encounter.patient_id == patient.id).order_by(Encounter.started_at.desc()).first())
    symptoms = db.query(Symptom).filter(Symptom.encounter_id == encounter.id).all() if encounter else []
    documents = db.query(Document).filter(Document.patient_id == patient.id).all()
    consultations_query = db.query(Consultation).filter(Consultation.patient_id == patient.id)
    if encounter:
        consultations_query = consultations_query.filter(Consultation.encounter_id == encounter.id)

    enc_priority = getattr(encounter, "priority", "routine") or "routine"
    enc_red_flag = getattr(encounter, "red_flag_reason", None)

    ocr_findings, medical_extraction, intelligence = [], [], []
    for document in documents:
        result = db.query(OCRResult).filter(OCRResult.document_id == document.id).order_by(OCRResult.id.desc()).first()
        if result:
            ocr_findings.append({"ocr_result_id": result.id, "source_document_id": document.id,
                                 "ocr_status": document.ocr_status, "has_extracted_text": result.extracted_text is not None,
                                 "source": "automated_ocr", "physician_verified": False})
        extraction = _extraction(document, result)
        if extraction is None or result is None:
            continue
        medical_extraction.append({"source_document_id": document.id, "ocr_result_id": result.id,
            "source": "automated_extraction", "physician_verified": False,
            "observations": [x.model_dump() for x in extraction.observations],
            "medications": [x.model_dump() for x in extraction.medications],
            "allergies": [x.model_dump() for x in extraction.allergies],
            "diagnoses_or_conditions": [x.model_dump() for x in extraction.diagnoses_or_conditions],
            "clinical_notes": [x.model_dump() for x in extraction.clinical_notes]})
        info = build_document_intelligence(document.id, result.id, extraction)
        intelligence.append({"source_document_id": document.id, "ocr_result_id": result.id,
            "source": "deterministic_document_intelligence", "physician_verified": False,
            "observations": [x.model_dump() for x in info.highlighted_observations],
            "timeline": [x.model_dump() for x in info.timeline]})

    ayush_data = map_ayush_codes(db, patient.id, encounter.id if encounter else None).model_dump()
    red_flags_list = [{"reason": enc_red_flag, "severity": "high"}] if enc_red_flag else []

    return {
        "patient": {"patient_id": patient.id, "name": patient.name, "age": patient.age, "sex": patient.gender},
        "encounter": {
            "encounter_id": encounter.id,
            "started_at": encounter.started_at,
            "chief_complaint": encounter.chief_complaint,
            "priority": enc_priority,
            "red_flag_reason": enc_red_flag,
        } if encounter else None,
        "priority": enc_priority,
        "red_flag_reason": enc_red_flag,
        "ayush_coding": ayush_data,
        "symptoms": [{"symptom_id": x.id, "name": x.name, "duration": x.duration, "severity": x.severity, "location": x.location, "description": x.description, "source": "patient_history", "physician_verified": False} for x in symptoms],
        "medications": [{"medication_id": x.id, "name": x.name, "dosage": x.dosage, "frequency": x.frequency, "source": "patient_history", "physician_verified": False} for x in db.query(Medication).filter(Medication.patient_id == patient.id).all()],
        "allergies": [{"allergy_id": x.id, "substance": x.allergen, "reaction": x.reaction, "severity": x.severity, "source": "patient_history", "physician_verified": False} for x in db.query(Allergy).filter(Allergy.patient_id == patient.id).all()],
        "red_flags": red_flags_list,
        "documents": [{"document_id": x.id, "document_type": x.document_type, "filename": x.file_name, "ocr_status": x.ocr_status} for x in documents],
        "ocr_findings": ocr_findings,
        "medical_extraction": medical_extraction,
        "document_intelligence": intelligence,
        "clinical_summary": {"available": False, "source": "not_generated", "content": None, "physician_verified": False, "notice": "No clinical summary is persisted. D3 does not call AI or generate a new summary."},
        "consultations": [{
            "consultation_id": x.id,
            "encounter_id": x.encounter_id,
            "review_status": x.review_status,
            "priority": getattr(x, "priority", "routine") or enc_priority,
            "red_flag_reason": getattr(x, "red_flag_reason", None) or enc_red_flag,
            "physician_notes": x.physician_notes,
            "existing_notes": x.notes,
            "physician_id": x.physician_id,
            "reviewed_at": x.reviewed_at,
            "physician_id_authenticated": False,
        } for x in consultations_query.all()],
        "physician_verification_notice": "All source, OCR, extraction, intelligence, and AI-generated information is not physician verified unless recorded by a separate D3 verification event. physician_id is not authenticated.",
    }

