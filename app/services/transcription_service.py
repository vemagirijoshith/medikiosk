import os
from typing import Optional

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


async def transcribe_audio(
    file_bytes: bytes,
    filename: str = "recording.webm",
    content_type: str = "audio/webm",
    language: Optional[str] = None,
) -> str:
    """
    Transcribes audio bytes using Groq Whisper (whisper-large-v3-turbo).
    """
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise AIAuthenticationError("AI provider credentials are not configured")

    base_url = os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
    model = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=0)

    kwargs = {
        "file": (filename, file_bytes, content_type),
        "model": model,
        "temperature": 0.0,
    }

    # ISO-639-1 language code mapping if provided
    lang_code = None
    if language:
        clean_lang = language.lower().strip()
        if clean_lang in {"en", "hi", "te", "ta", "bn", "mr", "gu", "kn", "ml", "pa", "ur"}:
            lang_code = clean_lang
        elif "-" in clean_lang:
            lang_code = clean_lang.split("-")[0]

    if lang_code:
        kwargs["language"] = lang_code

    try:
        response = await client.audio.transcriptions.create(**kwargs)
    except APITimeoutError as exc:
        raise AITimeoutError("Transcription request timed out") from exc
    except APIConnectionError as exc:
        raise AIConnectionError("Transcription service could not be reached") from exc
    except APIStatusError as exc:
        if exc.status_code in (401, 403):
            raise AIAuthenticationError("Transcription service authentication failed") from exc
        if exc.status_code == 429:
            raise AIRateLimitError("Transcription service is temporarily rate-limited") from exc
        raise AIUpstreamError(f"Transcription service error: {exc.message}") from exc
    except Exception as exc:
        raise AIUpstreamError("Unexpected transcription error") from exc

    text = getattr(response, "text", "")
    return text.strip()
