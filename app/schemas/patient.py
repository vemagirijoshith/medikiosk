from pydantic import BaseModel, Field


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