import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)
from app.schemas.clinical_summary import ClinicalSummary

load_dotenv()


SUMMARY_SYSTEM_PROMPT = """
You are generating a physician-facing clinical history summary from verified
patient-provided and document-extracted information.

Use ONLY the supplied information. Do not invent, infer, diagnose, prescribe,
recommend treatment, recommend tests, or provide medical advice. If information
is missing, state that it is unavailable or use null/empty lists. Preserve
uncertainty. Do not convert abnormal findings into diagnoses. Preserve source
traceability and do not create new dates, numbers, medications, allergies,
conditions, or document IDs.

Return only valid JSON matching the supplied summary structure. The generated
summary is editable and must never replace the source facts.
""".strip()


def _parse_summary(raw: str) -> ClinicalSummary:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()
    try:
        return ClinicalSummary.model_validate(json.loads(candidate))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError("AI returned invalid clinical summary data") from exc


def _check_supported(summary: ClinicalSummary, source: dict[str, Any]) -> None:
    source_medications = {item["name"].casefold() for item in source["medications"]}
    source_allergies = {item["substance"].casefold() for item in source["allergies"]}
    source_conditions = {item.casefold() for item in source["diagnoses_or_conditions"]}
    source_documents = set(source["document_ids"])
    if any(item.name.casefold() not in source_medications for item in summary.medications):
        raise ValueError("summary contains an unsupported medication")
    if any(item.substance.casefold() not in source_allergies for item in summary.allergies):
        raise ValueError("summary contains an unsupported allergy")
    if any(item.casefold() not in source_conditions for item in summary.diagnoses_or_conditions):
        raise ValueError("summary contains an unsupported diagnosis or condition")
    if any(item.document_id not in source_documents for item in summary.observations + summary.relevant_document_findings):
        raise ValueError("summary contains an unsupported document ID")
    source_dates = {item for item in source["document_dates"] if item}
    if any(item.date and item.date not in source_dates for item in summary.timeline):
        raise ValueError("summary contains an unsupported date")


async def generate_clinical_summary(source: dict[str, Any]) -> ClinicalSummary:
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    if not api_key:
        raise AIAuthenticationError("AI provider credentials are not configured")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=0)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(source, ensure_ascii=True)},
            ],
            temperature=0,
        )
    except APITimeoutError as exc:
        raise AITimeoutError("AI provider request timed out") from exc
    except APIConnectionError as exc:
        raise AIConnectionError("AI provider could not be reached") from exc
    except APIStatusError as exc:
        if exc.status_code in (401, 403):
            raise AIAuthenticationError("AI provider authentication failed") from exc
        if exc.status_code == 429:
            raise AIRateLimitError("AI provider is temporarily rate-limited") from exc
        raise AIUpstreamError("AI provider returned an error") from exc
    try:
        raw = response.choices[0].message.content
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("empty summary")
        summary = _parse_summary(raw)
        _check_supported(summary, source)
        return summary
    except (AttributeError, IndexError, TypeError) as exc:
        raise AIUpstreamError("AI provider returned an invalid response") from exc
    except ValueError as exc:
        raise ValueError(str(exc)) from exc