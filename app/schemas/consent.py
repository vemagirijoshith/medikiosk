from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ConsentPurpose = Literal[
    "clinical_history",
    "document_processing",
    "document_extraction",
    "clinical_summary",
    "physician_review",
    "abdm_sharing",
]


class ConsentStatus(str):
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentGrantRequest(BaseModel):
    action: Literal["grant"]
    purpose: ConsentPurpose
    consent_version: str = Field(min_length=1, max_length=50)
    source: str | None = Field(default=None, max_length=50)
    metadata: str | None = Field(default=None, max_length=1000)


class ConsentRevokeRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    purpose: str
    status: str
    consent_version: str
    created_at: datetime
    revoked_at: datetime | None
    source: str | None
    metadata: str | None = Field(default=None, validation_alias="audit_metadata", serialization_alias="metadata")


class ConsentListResponse(BaseModel):
    consents: list[ConsentResponse]


class ConsentCheckResponse(BaseModel):
    patient_id: int
    purpose: str
    has_consent: bool
    status: str | None
    consent_version: str | None
    granted_at: datetime | None
    revoked_at: datetime | None