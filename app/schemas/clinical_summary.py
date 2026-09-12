from typing import Literal

from pydantic import BaseModel, ConfigDict


class SummaryPatient(BaseModel):
    name: str | None = None
    age: str | None = None
    sex: str | None = None
    patient_id: str | None = None


class SummaryEncounter(BaseModel):
    encounter_id: int
    chief_complaint: str | None = None
    encounter_date: str | None = None


class SummarySymptom(BaseModel):
    name: str
    details: str | None = None
    source: Literal["patient_history", "document"]


class SummaryMedication(BaseModel):
    name: str
    dose: str | None = None
    frequency: str | None = None
    source: Literal["patient_history", "document"]


class SummaryAllergy(BaseModel):
    substance: str
    reaction: str | None = None
    source: Literal["patient_history", "document"]


class SummaryDocumentFinding(BaseModel):
    document_id: int
    date: str | None = None
    finding: str
    source_text: str | None = None


class SummaryObservation(BaseModel):
    document_id: int
    name: str
    value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: Literal["low", "normal", "high", "unknown"] = "unknown"
    source_text: str | None = None


class SummaryTimelineEvent(BaseModel):
    date: str | None = None
    event: str
    source: str


class SummaryRedFlag(BaseModel):
    type: str
    severity: str
    message: str
    source: str | None = None


class ClinicalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient: SummaryPatient
    encounter: SummaryEncounter
    history_of_present_illness: str | None = None
    symptoms: list[SummarySymptom]
    medications: list[SummaryMedication]
    allergies: list[SummaryAllergy]
    relevant_document_findings: list[SummaryDocumentFinding]
    observations: list[SummaryObservation]
    timeline: list[SummaryTimelineEvent]
    red_flags: list[SummaryRedFlag]
    diagnoses_or_conditions: list[str]
    summary: str


class ClinicalSummaryResponse(BaseModel):
    patient_id: int
    source_document_ids: list[int]
    generated_summary: ClinicalSummary