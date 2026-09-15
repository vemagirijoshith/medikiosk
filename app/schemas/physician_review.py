from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ReviewStatus = Literal["pending", "in_review", "verified", "completed"]


class PacketPatient(BaseModel):
    patient_id: int
    name: str
    age: int
    sex: str


class PacketEncounter(BaseModel):
    encounter_id: int
    started_at: datetime | None = None
    chief_complaint: str | None = None
    priority: str = "routine"
    red_flag_reason: str | None = None


class PacketDocument(BaseModel):
    document_id: int
    document_type: str | None = None
    filename: str
    ocr_status: str


class SourceItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: str
    source_document_id: int | None = None


class PacketConsultation(BaseModel):
    consultation_id: int
    encounter_id: int
    review_status: ReviewStatus
    priority: str = "routine"
    red_flag_reason: str | None = None
    physician_notes: str | None = None
    existing_notes: str | None = None
    physician_id: str | None = None
    reviewed_at: datetime | None = None
    physician_id_authenticated: Literal[False] = False


class ClinicalSummaryPacket(BaseModel):
    available: bool = False
    source: Literal["ai_generated", "not_generated"] = "not_generated"
    content: dict[str, Any] | None = None
    physician_verified: Literal[False] = False
    notice: str


class PhysicianReviewPacket(BaseModel):
    patient: PacketPatient
    encounter: PacketEncounter | None = None
    priority: str = "routine"
    red_flag_reason: str | None = None
    ayush_coding: dict[str, Any] | None = None
    symptoms: list[dict[str, Any]]
    medications: list[dict[str, Any]]
    allergies: list[dict[str, Any]]
    red_flags: list[dict[str, Any]]
    documents: list[PacketDocument]
    ocr_findings: list[dict[str, Any]]
    medical_extraction: list[dict[str, Any]]
    document_intelligence: list[dict[str, Any]]
    clinical_summary: ClinicalSummaryPacket
    consultations: list[PacketConsultation]
    physician_verification_notice: str



class PhysicianReviewNotesRequest(BaseModel):
    physician_id: str | None = Field(default=None, max_length=255)
    notes: str = Field(min_length=1, max_length=10000)


class PhysicianReviewVerifyRequest(BaseModel):
    physician_id: str | None = Field(default=None, max_length=255)
    verified_fields: list[Literal["symptoms", "medications", "allergies"]] = Field(min_length=1)


class PhysicianReviewCompleteRequest(BaseModel):
    physician_id: str | None = Field(default=None, max_length=255)


class PhysicianReviewActionResponse(BaseModel):
    consultation_id: int
    review_status: ReviewStatus
    physician_id_authenticated: Literal[False] = False
