from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)
from app.services.transcription_service import transcribe_audio


def completion(text):
    return SimpleNamespace(text=text)


@pytest.mark.asyncio
async def test_transcribe_audio_success(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-groq-key")
    fake_create = AsyncMock(return_value=completion("I have a fever and headache"))
    fake_client = SimpleNamespace(
        audio=SimpleNamespace(
            transcriptions=SimpleNamespace(create=fake_create)
        )
    )

    with patch("app.services.transcription_service.AsyncOpenAI", return_value=fake_client) as client_class:
        result = await transcribe_audio(
            b"fake audio data",
            filename="voice.webm",
            content_type="audio/webm",
            language="en",
        )

    assert result == "I have a fever and headache"
    client_class.assert_called_once()
    kwargs = fake_create.await_args.kwargs
    assert kwargs["model"] == "whisper-large-v3-turbo"
    assert kwargs["language"] == "en"
    assert kwargs["file"] == ("voice.webm", b"fake audio data", "audio/webm")


@pytest.mark.asyncio
async def test_transcribe_audio_missing_credentials(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(AIAuthenticationError):
        await transcribe_audio(b"audio")


def test_transcribe_endpoint_success(client):
    test_client, _ = client
    with patch("app.api.intake.transcribe_audio", new=AsyncMock(return_value="My chest hurts")):
        files = {"file": ("audio.webm", b"fake audio data", "audio/webm")}
        data = {"language": "en"}
        response = test_client.post("/intake/transcribe", files=files, data=data)

    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "My chest hurts"
    assert body["language"] == "en"


def test_transcribe_endpoint_empty_file(client):
    test_client, _ = client
    files = {"file": ("audio.webm", b"", "audio/webm")}
    response = test_client.post("/intake/transcribe", files=files)
    assert response.status_code == 400


def test_transcribe_endpoint_handles_upstream_error(client):
    test_client, _ = client
    with patch("app.api.intake.transcribe_audio", new=AsyncMock(side_effect=AIUpstreamError("Whisper failed"))):
        files = {"file": ("audio.webm", b"audio", "audio/webm")}
        response = test_client.post("/intake/transcribe", files=files)

    assert response.status_code == 502
