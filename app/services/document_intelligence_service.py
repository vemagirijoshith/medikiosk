import re
from collections.abc import Mapping
from typing import Any, Iterable

from app.schemas.document_intelligence import (
    DocumentIntelligenceResponse,
    HighlightedObservation,
    TimelineEntry,
    TimelineEvent,
)
from app.schemas.medical_extraction import MedicalExtraction


_NUMBER = r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)"


def _single_number(value: str | None) -> float | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if re.search(rf"{_NUMBER}\s*/\s*{_NUMBER}", candidate):
        return None
    match = re.fullmatch(rf"(?:<|>)?\s*({_NUMBER})(?:\s*[A-Za-z%/]+)?", candidate)
    return float(match.group(1)) if match else None


def _reference_bounds(reference_range: str | None) -> tuple[float | None, float | None, str] | None:
    if not isinstance(reference_range, str):
        return None
    candidate = reference_range.strip()
    range_match = re.search(rf"({_NUMBER})\s*(?:-|–|to)\s*({_NUMBER})", candidate, re.IGNORECASE)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2)), "range"
    comparison = re.search(rf"(<=|>=|<|>)\s*({_NUMBER})", candidate)
    if comparison:
        operator, number = comparison.groups()
        value = float(number)
        if operator in ("<", "<="):
            return None, value, operator
        return value, None, operator
    return None


def _status(value: str | None, reference_range: str | None) -> str:
    numeric_value = _single_number(value)
    bounds = _reference_bounds(reference_range)
    if numeric_value is None or bounds is None:
        return "unknown"
    lower, upper, kind = bounds
    if kind == "range":
        if lower is None or upper is None:
            return "unknown"
        if numeric_value < lower:
            return "low"
        if numeric_value > upper:
            return "high"
        return "normal"
    if kind in ("<", "<="):
        return "normal" if numeric_value <= upper else "high"
    return "normal" if numeric_value >= lower else "low"


def _validated_extraction(extraction: MedicalExtraction | Mapping[str, Any]) -> MedicalExtraction:
    if isinstance(extraction, MedicalExtraction):
        return extraction
    return MedicalExtraction.model_validate(extraction)


def build_document_intelligence(
    document_id: int,
    ocr_result_id: int,
    extraction: MedicalExtraction | Mapping[str, Any],
) -> DocumentIntelligenceResponse:
    validated = _validated_extraction(extraction)
    document_date = validated.document.document_date
    document_type = validated.document.document_type
    events: list[TimelineEvent] = []
    highlighted: list[HighlightedObservation] = []

    for observation in validated.observations:
        status = _status(observation.value, observation.reference_range)
        event = TimelineEvent(
            category="observation",
            name=observation.name,
            value=observation.value,
            unit=observation.unit,
            reference_range=observation.reference_range,
            status=status,
            source_text=observation.source_text,
        )
        events.append(event)
        highlighted.append(
            HighlightedObservation(
                document_id=document_id,
                name=observation.name,
                value=observation.value,
                unit=observation.unit,
                reference_range=observation.reference_range,
                status=status,
                source_text=observation.source_text,
            )
        )

    for medication in validated.medications:
        events.append(TimelineEvent(
            category="medication",
            name=medication.name,
            value=medication.dose,
            source_text=medication.source_text,
        ))
    for allergy in validated.allergies:
        events.append(TimelineEvent(
            category="allergy",
            name=allergy.substance,
            value=allergy.reaction,
            source_text=allergy.source_text,
        ))
    for item in validated.diagnoses_or_conditions:
        events.append(TimelineEvent(category="diagnosis_or_condition", name=item.text, source_text=item.source_text))
    for item in validated.procedures:
        events.append(TimelineEvent(category="procedure", name=item.text, source_text=item.source_text))
    for item in validated.clinical_notes:
        events.append(TimelineEvent(category="clinical_note", name=item.text, source_text=item.source_text))

    timeline = [TimelineEntry(
        date=document_date,
        document_id=document_id,
        document_type=document_type,
        events=events,
    )]
    return DocumentIntelligenceResponse(
        timeline=timeline,
        highlighted_observations=highlighted,
        extraction_metadata={
            "document_id": document_id,
            "ocr_result_id": ocr_result_id,
            "document_date": document_date,
            "document_type": document_type,
        },
    )


def build_timeline(
    documents: Iterable[tuple[int, int, MedicalExtraction | Mapping[str, Any]]],
) -> list[TimelineEntry]:
    entries = [
        build_document_intelligence(document_id, ocr_result_id, extraction).timeline[0]
        for document_id, ocr_result_id, extraction in documents
    ]
    return sorted(entries, key=lambda entry: (entry.date is None, entry.date or ""))