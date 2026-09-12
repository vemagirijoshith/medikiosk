from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Consent, Encounter, Patient
from app.schemas.abdm import ABDMExportRequest, ABDMExportResponse, ABHALinkRequest, ABHALinkResponse
from app.services.abdm_service import ABDM_PURPOSE, ABDMConfigurationError, ABDMService
from app.services.consent_service import get_consent, has_active_consent


router = APIRouter(prefix="/patients", tags=["ABDM Foundation"])
service = ABDMService()


@router.put("/{patient_id}/abha", response_model=ABHALinkResponse)
def link_abha(patient_id: int, request: ABHALinkRequest, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    try:
        abha_id = service.link_abha(db, patient, request.abha_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ABHALinkResponse(patient_id=patient_id, abha_id=abha_id, status="linked")


@router.post("/{patient_id}/abdm/export", response_model=ABDMExportResponse)
def export_health_record(
    patient_id: int,
    request: ABDMExportRequest,
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    encounter = None
    if request.encounter_id is not None:
        encounter = db.get(Encounter, request.encounter_id)
        if encounter is None or encounter.patient_id != patient_id:
            raise HTTPException(status_code=404, detail="Encounter not found")

    consent = get_consent(db, patient_id, ABDM_PURPOSE)
    if not has_active_consent(db, patient_id, ABDM_PURPOSE):
        service.record_blocked_export(db, patient_id, request.encounter_id)
        raise HTTPException(status_code=403, detail="Active ABDM sharing consent is required")
    if not patient.abha_id:
        raise HTTPException(status_code=422, detail="Patient does not have a locally linked ABHA ID")

    try:
        service.validate_configuration()
    except ABDMConfigurationError as exc:
        raise HTTPException(status_code=503, detail="ABDM integration is not configured") from exc
    result = service.prepare_sandbox_export(db, patient, encounter, consent)
    return ABDMExportResponse(**result)