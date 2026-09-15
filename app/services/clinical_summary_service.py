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

Return only valid JSON matching this exact structure:
{
  "patient": {"name": str or null, "age": str or null, "sex": str or null, "patient_id": str or null},
  "encounter": {"encounter_id": int, "chief_complaint": str or null, "encounter_date": str or null},
  "history_of_present_illness": str or null,
  "symptoms": [{"name": str, "details": str or null, "source": "patient_history" or "document"}],
  "medications": [{"name": str, "dose": str or null, "frequency": str or null, "source": "patient_history" or "document"}],
  "allergies": [{"substance": str, "reaction": str or null, "source": "patient_history" or "document"}],
  "relevant_document_findings": [{"document_id": int, "date": str or null, "finding": str, "source_text": str or null}],
  "observations": [{"document_id": int, "name": str, "value": str or null, "unit": str or null, "reference_range": str or null, "status": "low"|"normal"|"high"|"unknown", "source_text": str or null}],
  "timeline": [{"date": str or null, "event": str, "source": str}],
  "red_flags": [{"type": str, "severity": str, "message": str, "source": str or null}],
  "diagnoses_or_conditions": [str],
  "summary": str
}

Do NOT output extra keys such as "documents", "document_ids", or "document_dates". All list fields must be included as arrays (use [] if empty).
The generated summary is editable and must never replace the source facts.
""".strip()


def _parse_summary(raw: str, source: dict[str, Any] | None = None) -> ClinicalSummary:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()
    try:
        data = json.loads(candidate)
        if not isinstance(data, dict):
            raise ValueError("AI returned invalid clinical summary data")
        if not data:
            raise ValueError("empty summary")

        # Sanitize extra keys that LLM might echo from source input
        for extra_key in ["documents", "document_ids", "document_dates"]:
            data.pop(extra_key, None)

        # Ensure all required list fields default to empty list if missing
        for list_field in [
            "symptoms",
            "medications",
            "allergies",
            "relevant_document_findings",
            "observations",
            "timeline",
            "red_flags",
            "diagnoses_or_conditions",
        ]:
            if list_field not in data or data[list_field] is None:
                data[list_field] = []

        # Populate patient and encounter if missing or incomplete
        if source:
            if not data.get("patient"):
                data["patient"] = source.get("patient", {})
            if not data.get("encounter"):
                data["encounter"] = source.get("encounter", {})

            # Filter hallucinated medications not present in source facts
            valid_meds = {m["name"].casefold() for m in source.get("medications", []) if isinstance(m, dict) and "name" in m}
            if "medications" in data and isinstance(data["medications"], list):
                data["medications"] = [m for m in data["medications"] if isinstance(m, dict) and m.get("name", "").casefold() in valid_meds]

            # Filter hallucinated allergies not present in source facts
            valid_allergies = {a["substance"].casefold() for a in source.get("allergies", []) if isinstance(a, dict) and "substance" in a}
            if "allergies" in data and isinstance(data["allergies"], list):
                data["allergies"] = [a for a in data["allergies"] if isinstance(a, dict) and a.get("substance", "").casefold() in valid_allergies]

            # Filter hallucinated conditions not present in source facts
            valid_conditions = {c.casefold() for c in source.get("diagnoses_or_conditions", []) if isinstance(c, str)}
            if "diagnoses_or_conditions" in data and isinstance(data["diagnoses_or_conditions"], list):
                data["diagnoses_or_conditions"] = [c for c in data["diagnoses_or_conditions"] if isinstance(c, str) and c.casefold() in valid_conditions]

            # Filter hallucinated document findings/observations
            valid_docs = set(source.get("document_ids", []))
            if "relevant_document_findings" in data and isinstance(data["relevant_document_findings"], list):
                data["relevant_document_findings"] = [f for f in data["relevant_document_findings"] if isinstance(f, dict) and f.get("document_id") in valid_docs]
            if "observations" in data and isinstance(data["observations"], list):
                data["observations"] = [o for o in data["observations"] if isinstance(o, dict) and o.get("document_id") in valid_docs]

            # Sanitize timeline dates against known document dates and encounter date
            valid_dates = {d for d in source.get("document_dates", []) if d}
            encounter_date = (source.get("encounter") or {}).get("encounter_date")
            if encounter_date:
                valid_dates.add(encounter_date)
            if "timeline" in data and isinstance(data["timeline"], list):
                for ev in data["timeline"]:
                    if isinstance(ev, dict) and ev.get("date") and ev.get("date") not in valid_dates:
                        ev["date"] = None

        # Ensure non-empty summary narrative
        if not data.get("summary"):
            pt_name = (data.get("patient") or {}).get("name") or "Patient"
            data["summary"] = f"Clinical intake recorded for {pt_name}."

        return ClinicalSummary.model_validate(data)
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
    encounter_date = (source.get("encounter") or {}).get("encounter_date")
    if encounter_date:
        source_dates.add(encounter_date)
    if any(item.date and item.date not in source_dates for item in summary.timeline):
        raise ValueError("summary contains an unsupported date")


async def generate_clinical_summary(source: dict[str, Any]) -> ClinicalSummary:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise AIAuthenticationError("AI provider credentials are not configured")

    if api_key.startswith("gsk_"):
        base_url = os.getenv("GROQ_BASE_URL") or os.getenv("NVIDIA_BASE_URL") or "https://api.groq.com/openai/v1"
        model = os.getenv("GROQ_MODEL") or os.getenv("NVIDIA_MODEL") or "openai/gpt-oss-120b"
    else:
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=0)
    
    completion_kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(source, ensure_ascii=True)},
        ],
        "temperature": 0,
    }
    if api_key.startswith("gsk_"):
        completion_kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await client.chat.completions.create(**completion_kwargs)
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
        summary = _parse_summary(raw, source=source)
        _check_supported(summary, source)
        return summary
    except (AttributeError, IndexError, TypeError) as exc:
        raise AIUpstreamError("AI provider returned an invalid response") from exc
    except ValueError as exc:
        raise ValueError(str(exc)) from exc