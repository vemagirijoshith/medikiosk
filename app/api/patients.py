from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse


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


@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return patient