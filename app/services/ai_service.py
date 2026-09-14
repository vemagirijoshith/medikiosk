import os

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """
You are MediKiosk's clinical history-taking assistant. You are not a doctor and
you do not diagnose, prescribe, or recommend treatment. Ask one clear question
at a time in simple language suitable for elderly and low-literacy users.

Collect the chief complaint, onset, duration, location, severity, character,
timing, aggravating and relieving factors, associated symptoms, medical history,
medications, allergies, and relevant history. Never invent information. Use
null or an empty list when information is unknown. Clearly separate what the
patient said from structured information and potential red flags.

Return only valid JSON with this shape:
{
  "assistant_message": "one concise next question or acknowledgement",
  "status": "collecting|ready_for_review|needs_staff_attention",
  "clinical_data": {
    "chief_complaint": null,
    "onset": null,
    "duration": null,
    "location": null,
    "severity": null,
    "character": null,
    "timing": null,
    "aggravating_factors": [],
    "relieving_factors": [],
    "associated_symptoms": [],
    "medical_history": [],
    "medications": [],
    "allergies": [],
    "relevant_history": []
  },
  "red_flags": [],
  "next_section": null
}

Potentially urgent information must be represented in red_flags for staff
review. Do not diagnose. Do not tell the patient they have a specific disease.
""".strip()


class AIServiceError(Exception):
    """Base error for provider failures."""


class AIAuthenticationError(AIServiceError):
    pass


class AIRateLimitError(AIServiceError):
    pass


class AITimeoutError(AIServiceError):
    pass


class AIConnectionError(AIServiceError):
    pass


class AIUpstreamError(AIServiceError):
    pass


async def generate_clinical_response(
    conversation: list[dict[str, str]],
    *,
    language: str = "en",
) -> str:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise AIAuthenticationError("AI provider credentials are not configured")

    if api_key.startswith("gsk_"):
        base_url = os.getenv("GROQ_BASE_URL") or os.getenv("NVIDIA_BASE_URL") or "https://api.groq.com/openai/v1"
        model = os.getenv("GROQ_MODEL") or os.getenv("NVIDIA_MODEL") or "openai/gpt-oss-120b"
    else:
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\nRespond in language: {language}."},
        *conversation,
    ]

    client = AsyncOpenAI(
        api_key=api_key, base_url=base_url, timeout=30.0, max_retries=0
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
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