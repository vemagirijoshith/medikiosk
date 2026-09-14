import os

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)

load_dotenv()


EXTRACTION_SYSTEM_PROMPT = """
You extract medical information from OCR text for physician verification.
Extraction is not diagnosis, interpretation, treatment, or medical advice.

Extract ONLY information explicitly present in the OCR text. Never guess,
infer, normalize, complete, or invent missing values. Preserve uncertainty and
the original wording when OCR confidence is low. If a value is absent, use null
or an empty array. A diagnosis_or_condition is allowed only when it is written
explicitly in the source document; do not diagnose from observations.

Return ONLY valid JSON with exactly these top-level fields:
patient, document, observations, medications, allergies,
diagnoses_or_conditions, procedures, clinical_notes.

Every extracted item should include source_text when possible. Do not generate
confidence scores. Do not provide treatment, prescriptions, recommendations, or
medical advice.
""".strip()


async def generate_medical_extraction(ocr_text: str) -> str:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise AIAuthenticationError("AI provider credentials are not configured")

    if api_key.startswith("gsk_"):
        base_url = os.getenv("GROQ_BASE_URL") or os.getenv("NVIDIA_BASE_URL") or "https://api.groq.com/openai/v1"
        model = os.getenv("GROQ_MODEL") or os.getenv("NVIDIA_MODEL") or "openai/gpt-oss-120b"
    else:
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

    client = AsyncOpenAI(
        api_key=api_key, base_url=base_url, timeout=30.0, max_retries=0
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"OCR TEXT:\n{ocr_text}"},
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
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise AIUpstreamError("AI provider returned an invalid response") from exc
    if not isinstance(content, str) or not content.strip():
        raise AIUpstreamError("AI provider returned an empty response")
    return content