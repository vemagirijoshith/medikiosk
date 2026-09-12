from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.consent import Consent
from app.models.patient import Patient
from app.schemas.consent import (
    ConsentCheckResponse,
    ConsentGrantRequest,
    ConsentListResponse,
    ConsentRevokeRequest,
    ConsentResponse,
)
from app.services.consent_service import (
    get_all_consents,
    get_consent,
    grant_consent,
    has_active_consent,
    revoke_consent,
)

router = APIRouter(prefix="/patients", tags=["Consents"])


@router.post(
    "/{patient_id}/consents",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant consent for a specific purpose"
)
def grant_consent_endpoint(
    patient_id: int,
    request: ConsentGrantRequest,
    db: Session = Depends(get_db)
):
    """Grant consent for a specific purpose."""
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consent = grant_consent(
        db=db,
        patient_id=patient_id,
        purpose=request.purpose,
        consent_version=request.consent_version,
        source=request.source,
        metadata=request.metadata
    )
    return consent


@router.get(
    "/{patient_id}/consents",
    response_model=ConsentListResponse,
    summary="Get all consent records for a patient"
)
def get_consents_endpoint(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get all consent records for a patient."""
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consents = get_all_consents(db, patient_id)
    return {"consents": consents}


@router.get(
    "/{patient_id}/consents/check",
    response_model=ConsentCheckResponse,
    summary="Check if patient has active consent for a purpose"
)
def check_consent_endpoint(
    patient_id: int,
    purpose: str,
    db: Session = Depends(get_db)
):
    """Check if patient has active consent for a specific purpose."""
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consent = get_consent(db, patient_id, purpose)
    has_consent = consent is not None and consent.status == "granted" and consent.granted
    
    return ConsentCheckResponse(
        patient_id=patient_id,
        purpose=purpose,
        has_consent=has_consent,
        status=consent.status if consent else None,
        consent_version=consent.consent_version if consent else None,
        granted_at=consent.created_at if consent else None,
        revoked_at=consent.revoked_at if consent else None
    )


@router.post(
    "/{patient_id}/consents/{consent_id}/revoke",
    response_model=ConsentResponse,
    summary="Revoke consent for a specific purpose"
)
def revoke_consent_endpoint(
    patient_id: int,
    consent_id: int,
    request: ConsentRevokeRequest,
    db: Session = Depends(get_db)
):
    """Revoke consent for a specific purpose."""
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consent = db.get(Consent, consent_id)
    if not consent or consent.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    if consent.status != "granted":
        raise HTTPException(status_code=400, detail="Consent is not active")
    
    revoked = revoke_consent(db, patient_id, consent.purpose, request.reason)
    return revoked