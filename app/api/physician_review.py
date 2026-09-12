from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Consultation, Patient, PhysicianReviewAudit
from app.schemas.physician_review import (
    PhysicianReviewActionResponse, PhysicianReviewCompleteRequest,
    PhysicianReviewNotesRequest, PhysicianReviewPacket, PhysicianReviewVerifyRequest,
)
from app.services.consent_service import has_active_consent
from app.services.physician_review_service import build_physician_review_packet

router = APIRouter(prefix="/patients", tags=["Physician Review"])


def _patient_with_consent(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not has_active_consent(db, patient_id, "physician_review"):
        raise HTTPException(status_code=403, detail="Active physician_review consent is required")
    return patient


def _consultation(db: Session, patient_id: int, consultation_id: int) -> Consultation:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None or consultation.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultation


def _audit(db: Session, consultation: Consultation, action: str, physician_id: str | None, metadata: dict | None = None) -> None:
    db.add(PhysicianReviewAudit(patient_id=consultation.patient_id, encounter_id=consultation.encounter_id,
        consultation_id=consultation.id, physician_id=physician_id, action=action,
        status=consultation.review_status, audit_metadata=metadata))


@router.get("/{patient_id}/physician-review-packet", response_model=PhysicianReviewPacket)
def get_physician_review_packet(patient_id: int, encounter_id: int | None = Query(None), db: Session = Depends(get_db)) -> dict:
    patient = _patient_with_consent(db, patient_id)
    if encounter_id is not None:
        # This intentionally returns 404 without revealing another patient's encounter.
        from app.models import Encounter
        if db.query(Encounter).filter(Encounter.id == encounter_id, Encounter.patient_id == patient_id).first() is None:
            raise HTTPException(status_code=404, detail="Encounter not found")
    return build_physician_review_packet(db, patient, encounter_id)


@router.post("/{patient_id}/consultations/{consultation_id}/review/notes", response_model=PhysicianReviewActionResponse)
def add_notes(patient_id: int, consultation_id: int, request: PhysicianReviewNotesRequest, db: Session = Depends(get_db)) -> dict:
    _patient_with_consent(db, patient_id)
    consultation = _consultation(db, patient_id, consultation_id)
    consultation.physician_notes = request.notes.strip()
    consultation.physician_id = request.physician_id
    consultation.review_status = "in_review"
    _audit(db, consultation, "notes_added", request.physician_id, {"consultation_id": consultation.id})
    db.commit()
    return {"consultation_id": consultation.id, "review_status": consultation.review_status, "physician_id_authenticated": False}


@router.post("/{patient_id}/consultations/{consultation_id}/review/verify", response_model=PhysicianReviewActionResponse)
def verify(patient_id: int, consultation_id: int, request: PhysicianReviewVerifyRequest, db: Session = Depends(get_db)) -> dict:
    _patient_with_consent(db, patient_id)
    consultation = _consultation(db, patient_id, consultation_id)
    if consultation.review_status == "completed":
        raise HTTPException(status_code=409, detail="Completed reviews cannot be changed")
    consultation.physician_id = request.physician_id
    consultation.review_status = "verified"
    _audit(db, consultation, "verified", request.physician_id, {"consultation_id": consultation.id, "verified_fields": sorted(set(request.verified_fields))})
    db.commit()
    return {"consultation_id": consultation.id, "review_status": consultation.review_status, "physician_id_authenticated": False}


@router.post("/{patient_id}/consultations/{consultation_id}/review/complete", response_model=PhysicianReviewActionResponse)
def complete(patient_id: int, consultation_id: int, request: PhysicianReviewCompleteRequest, db: Session = Depends(get_db)) -> dict:
    _patient_with_consent(db, patient_id)
    consultation = _consultation(db, patient_id, consultation_id)
    if consultation.review_status != "verified":
        raise HTTPException(status_code=409, detail="Review must be verified before completion")
    consultation.physician_id = request.physician_id or consultation.physician_id
    consultation.review_status = "completed"
    consultation.reviewed_at = datetime.now(timezone.utc)
    _audit(db, consultation, "completed", request.physician_id, {"consultation_id": consultation.id})
    db.commit()
    return {"consultation_id": consultation.id, "review_status": consultation.review_status, "physician_id_authenticated": False}
