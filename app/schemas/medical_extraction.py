from typing import Any

from pydantic import BaseModel, ConfigDict


class ExtractedPatient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    age: str | None = None
    sex: str | None = None
    patient_id: str | None = None


class ExtractedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_date: str | None = None
    document_type: str | None = None
    hospital: str | None = None
    doctor: str | None = None


class ExtractedObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: str | None = None
    source_text: str | None = None


class ExtractedMedication(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    duration: str | None = None
    source_text: str | None = None


class ExtractedAllergy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    substance: str
    reaction: str | None = None
    source_text: str | None = None


class ExtractedTextItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    source_text: str | None = None


class ExtractedProcedure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    date: str | None = None
    source_text: str | None = None


class MedicalExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient: ExtractedPatient
    document: ExtractedDocument
    observations: list[ExtractedObservation]
    medications: list[ExtractedMedication]
    allergies: list[ExtractedAllergy]
    diagnoses_or_conditions: list[ExtractedTextItem]
    procedures: list[ExtractedProcedure]
    clinical_notes: list[ExtractedTextItem]


class MedicalExtractionResponse(BaseModel):
    document_id: int
    ocr_result_id: int
    extraction: MedicalExtraction