from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Allergy, Document, Encounter, Medication, OCRResult, Patient, Symptom
from app.schemas.clinical_summary import ClinicalSummaryResponse
from app.schemas.medical_extraction import MedicalExtraction
from app.services.clinical_summary_service import generate_clinical_summary
from app.services.ai_service import AIAuthenticationError, AIConnectionError, AIRateLimitError, AITimeoutError, AIUpstreamError
from app.services.document_intelligence_service import build_document_intelligence

router = APIRouter(prefix="/patients", tags=["Clinical Summary"])


def _source_data(db: Session, patient: Patient, encounter: Encounter) -> dict:
    symptoms = db.query(Symptom).filter(Symptom.encounter_id == encounter.id).all()
    medications = db.query(Medication).filter(Medication.patient_id == patient.id).all()
    allergies = db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
    documents = db.query(Document).filter(Document.patient_id == patient.id).all()
    source_documents = []
    document_ids = []
    document_dates = []
    for document in documents:
        result = db.query(OCRResult).filter(OCRResult.document_id == document.id).order_by(OCRResult.id.desc()).first()
        extraction_data = (result.structured_data or {}).get("medical_extraction") if result else None
        if not extraction_data:
            continue
        extraction = MedicalExtraction.model_validate(extraction_data)
        intelligence = build_document_intelligence(document.id, result.id, extraction)
        document_ids.append(document.id)
        document_date = extraction.document.document_date
        document_dates.append(document_date)
        source_documents.append({
            "document_id": document.id,
            "date": document_date,
            "document_type": extraction.document.document_type,
            "observations": [item.model_dump() for item in extraction.observations],
            "medications": [item.model_dump() for item in extraction.medications],
            "allergies": [item.model_dump() for item in extraction.allergies],
            "diagnoses_or_conditions": [item.text for item in extraction.diagnoses_or_conditions],
            "findings": [item.model_dump() for item in intelligence.highlighted_observations],
            "timeline": [item.model_dump() for item in intelligence.timeline[0].events],
        })
    return {
        "patient": {"name": patient.name, "age": str(patient.age), "sex": patient.gender, "patient_id": str(patient.id)},
        "encounter": {"encounter_id": encounter.id, "chief_complaint": encounter.chief_complaint, "encounter_date": encounter.started_at.date().isoformat() if encounter.started_at else None},
        "symptoms": [{"name": item.name, "details": item.description or item.duration, "source": "patient_history"} for item in symptoms],
        "medications": [{"name": item.name, "dose": item.dosage, "frequency": item.frequency, "source": "patient_history"} for item in medications],
        "allergies": [{"substance": item.allergen, "reaction": item.reaction, "source": "patient_history"} for item in allergies],
        "documents": source_documents,
        "document_ids": document_ids,
        "document_dates": document_dates,
        "diagnoses_or_conditions": [condition for item in source_documents for condition in item["diagnoses_or_conditions"]],
        "red_flags": [],
    }


@router.get("/{patient_id}/clinical-summary", response_model=ClinicalSummaryResponse)
async def get_clinical_summary(
    patient_id: int,
    encounter_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> ClinicalSummaryResponse:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if encounter_id is not None:
        encounter = db.get(Encounter, encounter_id)
        if encounter is None or encounter.patient_id != patient_id:
            raise HTTPException(status_code=404, detail="Encounter not found")
    else:
        encounter = db.query(Encounter).filter(Encounter.patient_id == patient_id).order_by(Encounter.started_at.desc()).first()
        if encounter is None:
            raise HTTPException(status_code=404, detail="Encounter not found")
    source = _source_data(db, patient, encounter)
    try:
        summary = await generate_clinical_summary(source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="AI returned invalid clinical summary data.") from exc
    except AIAuthenticationError as exc:
        raise HTTPException(status_code=503, detail="AI provider authentication failed.") from exc
    except AIRateLimitError as exc:
        raise HTTPException(status_code=503, detail="AI provider is temporarily unavailable.") from exc
    except AITimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except AIConnectionError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not be reached.") from exc
    except AIUpstreamError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid response.") from exc
    return ClinicalSummaryResponse(patient_id=patient.id, source_document_ids=source["document_ids"], generated_summary=summary)