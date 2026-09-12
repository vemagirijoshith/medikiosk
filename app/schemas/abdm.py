from typing import Any

from pydantic import BaseModel, Field


class ABHALinkRequest(BaseModel):
    abha_id: str = Field(min_length=1, max_length=32)


class ABHALinkResponse(BaseModel):
    patient_id: int
    abha_id: str
    status: str
    verified: bool = False


class ABDMExportRequest(BaseModel):
    encounter_id: int | None = Field(default=None, gt=0)


class ABDMExportResponse(BaseModel):
    status: str
    abha_id: str
    consent_id: int
    record_count: int
    payload: dict[str, Any]
