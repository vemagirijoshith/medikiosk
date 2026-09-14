from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.consultation import Consultation
from app.models.encounter import Encounter
from app.models.patient import Patient
from app.schemas.patient import (
    ConsultationCreate,
    ConsultationResponse,
    PatientCreate,
    PatientResponse,
    PhysicianReviewListItem,
)


router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=201
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
):

    patient = Patient(
        name=patient_data.name,
        age=patient_data.age,
        gender=patient_data.gender,
        phone=patient_data.phone,
        abha_id=patient_data.abha_id,
        language=patient_data.language
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


@router.post(
    "/{patient_id}/consultations",
    response_model=ConsultationResponse,
    status_code=201,
    summary="Create the review record for a patient encounter",
)
def create_consultation(
    patient_id: int,
    request: ConsultationCreate,
    db: Session = Depends(get_db),
):
    """Create one pending physician-review record per encounter.

    This adds no clinical facts and deliberately does not imply physician review.
    """
    patient = db.get(Patient, patient_id)
    encounter = db.get(Encounter, request.encounter_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if encounter is None or encounter.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Encounter not found")
    consultation = (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient_id, Consultation.encounter_id == encounter.id)
        .first()
    )
    if consultation is None:
        consultation = Consultation(patient_id=patient_id, encounter_id=encounter.id)
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
    return consultation


@router.get(
    "/physician/reviews",
    response_model=list[PhysicianReviewListItem],
    summary="List locally pending physician review records for the demo dashboard",
)
def list_physician_reviews(db: Session = Depends(get_db)):
    records = (
        db.query(Consultation, Patient, Encounter)
        .join(Patient, Consultation.patient_id == Patient.id)
        .join(Encounter, Consultation.encounter_id == Encounter.id)
        .order_by(Consultation.created_at.desc())
        .all()
    )
    return [
        {
            "consultation_id": consultation.id,
            "patient_id": patient.id,
            "patient_name": patient.name,
            "encounter_id": encounter.id,
            "chief_complaint": encounter.chief_complaint,
            "review_status": consultation.review_status,
            "created_at": consultation.created_at,
        }
        for consultation, patient, encounter in records
    ]


@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
