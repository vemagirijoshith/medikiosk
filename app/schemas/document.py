from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.medical_extraction import MedicalExtractionResponse


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    encounter_id: int | None
    filename: str = Field(validation_alias=AliasChoices("filename", "file_name"))
    content_type: str
    file_size: int
    status: str = Field(validation_alias=AliasChoices("status", "ocr_status"))
    created_at: datetime


class DocumentMetadata(DocumentResponse):
    pass


class OCRResponse(BaseModel):
    document_id: int
    status: str
    extracted_text: str
    structured_data: dict


class DocumentExtractionResponse(MedicalExtractionResponse):
    pass