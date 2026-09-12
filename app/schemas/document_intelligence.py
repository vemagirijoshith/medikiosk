from typing import Literal

from pydantic import BaseModel, ConfigDict


ObservationStatus = Literal["low", "normal", "high", "unknown"]


class TimelineEvent(BaseModel):
    category: str
    name: str
    value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: ObservationStatus = "unknown"
    source_text: str | None = None


class TimelineEntry(BaseModel):
    date: str | None = None
    document_id: int
    document_type: str | None = None
    events: list[TimelineEvent]


class HighlightedObservation(BaseModel):
    document_id: int
    name: str
    value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: ObservationStatus
    source_text: str | None = None


class DocumentIntelligenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline: list[TimelineEntry]
    highlighted_observations: list[HighlightedObservation]
    extraction_metadata: dict[str, int | str | None]