from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


IntakeStatus = Literal["collecting", "ready_for_review", "needs_staff_attention"]


class RedFlag(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    message: str


class ClinicalOutput(BaseModel):
    assistant_message: str = Field(min_length=1)
    status: IntakeStatus
    clinical_data: dict[str, Any] = Field(default_factory=dict)
    red_flags: list[RedFlag] = Field(default_factory=list)
    next_section: str | None = None


class IntakeStartRequest(BaseModel):
    patient_id: int = Field(gt=0)
    language: str = Field(default="en", min_length=2, max_length=20)
    mode: str = Field(default="general", min_length=1, max_length=50)


class IntakeStartResponse(BaseModel):
    encounter_id: int
    assistant_message: str
    status: IntakeStatus


class IntakeMessageRequest(BaseModel):
    encounter_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be empty")
        return value


class IntakeMessageResponse(BaseModel):
    encounter_id: int
    assistant_message: str
    status: IntakeStatus
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    red_flags: list[RedFlag] = Field(default_factory=list)