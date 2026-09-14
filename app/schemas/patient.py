from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: str
    phone: str | None = None
    abha_id: str | None = None
    language: str = "en"


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    phone: str | None
    abha_id: str | None
    language: str

    class Config:
        from_attributes = True


class ConsultationCreate(BaseModel):
    """Create the review record for an existing patient encounter."""

    encounter_id: int = Field(gt=0)


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    encounter_id: int
    review_status: str
    created_at: datetime


class PhysicianReviewListItem(BaseModel):
    consultation_id: int
    patient_id: int
    patient_name: str
    encounter_id: int
    chief_complaint: str | None
    review_status: str
    created_at: datetime
