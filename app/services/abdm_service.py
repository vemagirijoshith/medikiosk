import os
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Allergy, Document, Encounter, Medication, OCRResult, Patient, Symptom
from app.models.abdm_share_audit import ABDMShareAudit
from app.models.consent import Consent
from app.services.consent_service import has_active_consent


ABDM_PURPOSE = "abdm_sharing"


class ABDMConfigurationError(Exception):
    pass


class ABDMConsentError(Exception):
    pass


class ABDMService:
    """Local ABDM boundary; no external ABDM calls are made in D2."""

    def __init__(self) -> None:
        self.base_url = os.getenv("ABDM_BASE_URL", "")
        self.client_id = os.getenv("ABDM_CLIENT_ID", "")
        self.sandbox_mode = os.getenv("ABDM_SANDBOX_MODE", "true").lower() == "true"

    def validate_configuration(self) -> None:
        if not self.sandbox_mode and not self.base_url:
            raise ABDMConfigurationError("Official ABDM configuration is not available")

    @staticmethod
    def normalize_abha_id(value: str) -> str:
        normalized = re.sub(r"[\s-]", "", value)
        if not re.fullmatch(r"\d{14}", normalized):
            raise ValueError("abha_id must contain 14 digits")
        return normalized

    def link_abha(self, db: Session, patient: Patient, abha_id: str) -> str:
        normalized = self.normalize_abha_id(abha_id)
        existing = db.query(Patient).filter(
            Patient.abha_id == normalized, Patient.id != patient.id
        ).first()
        if existing:
            raise ValueError("ABHA identifier is already linked")
        patient.abha_id = normalized
        db.commit()
        db.refresh(patient)
        return normalized

    def _document_payload(self, db: Session, document: Document) -> dict[str, Any]:
        result = db.query(OCRResult).filter(
            OCRResult.document_id == document.id
        ).order_by(OCRResult.id.desc()).first()
        return {
            "document_id": document.id,
            "encounter_id": document.encounter_id,
            "document_type": document.document_type,
            "document_date": document.document_date.isoformat() if document.document_date else None,
            "ocr_status": document.ocr_status,
            "ocr": result.structured_data if result else None,
        }

    def build_export_payload(
        self, db: Session, patient: Patient, encounter: Encounter | None
    ) -> dict[str, Any]:
        encounters = [encounter] if encounter else db.query(Encounter).filter(
            Encounter.patient_id == patient.id
        ).order_by(Encounter.started_at.desc()).all()
        encounter_ids = {item.id for item in encounters}
        documents = db.query(Document).filter(Document.patient_id == patient.id).all()
        if encounter:
            documents = [item for item in documents if item.encounter_id in (None, encounter.id)]
        return {
            "patient": {"patient_id": patient.id, "abha_id": patient.abha_id, "name": patient.name},
            "encounters": [
                {
                    "encounter_id": item.id,
                    "chief_complaint": item.chief_complaint,
                    "language": item.language,
                    "status": item.status,
                    "started_at": item.started_at.isoformat() if item.started_at else None,
                    "symptoms": [
                        {"name": symptom.name, "duration": symptom.duration, "severity": symptom.severity,
                         "location": symptom.location, "description": symptom.description}
                        for symptom in db.query(Symptom).filter(Symptom.encounter_id == item.id).all()
                    ],
                }
                for item in encounters
            ],
            "medications": [
                {"name": item.name, "dosage": item.dosage, "frequency": item.frequency, "source": item.source}
                for item in db.query(Medication).filter(Medication.patient_id == patient.id).all()
            ],
            "allergies": [
                {"allergen": item.allergen, "reaction": item.reaction, "severity": item.severity}
                for item in db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
            ],
            "documents": [self._document_payload(db, item) for item in documents],
            "provenance": {
                "patient_id": patient.id,
                "encounter_ids": sorted(encounter_ids),
                "document_ids": [item.id for item in documents],
                "source": "MediKiosk local structured records",
            },
        }

    def prepare_sandbox_export(
        self, db: Session, patient: Patient, encounter: Encounter | None, consent: Consent
    ) -> dict[str, Any]:
        if not has_active_consent(db, patient.id, ABDM_PURPOSE):
            raise ABDMConsentError("Active ABDM sharing consent is required")
        payload = self.build_export_payload(db, patient, encounter)
        audit = ABDMShareAudit(
            patient_id=patient.id,
            encounter_id=encounter.id if encounter else None,
            consent_id=consent.id,
            action="sandbox_export_prepared",
            status="sandbox_ready",
            audit_metadata={"record_count": len(payload["documents"])},
        )
        db.add(audit)
        db.commit()
        return {"status": "sandbox_ready", "abha_id": patient.abha_id, "consent_id": consent.id,
                "record_count": len(payload["documents"]), "payload": payload}

    def record_blocked_export(
        self, db: Session, patient_id: int, encounter_id: int | None = None
    ) -> None:
        db.add(ABDMShareAudit(
            patient_id=patient_id,
            encounter_id=encounter_id,
            action="export_blocked_no_consent",
            status="blocked",
        ))
        db.commit()
