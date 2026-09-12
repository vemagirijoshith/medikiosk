from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
    SYSTEM_PROMPT,
    generate_clinical_response,
)


def completion_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def provider_error(status_code: int):
    import httpx

    request = httpx.Request("POST", "https://example.test/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return APIStatusError("provider error", response=response, body=None)


@pytest.mark.asyncio
async def test_success_uses_nvidia_configuration_and_messages(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    fake_create = AsyncMock(return_value=completion_response("{\"status\":\"collecting\"}"))
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )

    with patch("app.services.ai_service.AsyncOpenAI", return_value=fake_client) as client_class:
        result = await generate_clinical_response(
            [{"role": "user", "content": "I have fever."}], language="en"
        )

    assert result == '{"status":"collecting"}'
    client_class.assert_called_once_with(
        api_key="synthetic-test-key",
        base_url="https://integrate.api.nvidia.com/v1",
        timeout=30.0,
        max_retries=0,
    )
    call = fake_create.await_args.kwargs
    assert call["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert call["messages"][0]["role"] == "system"
    assert SYSTEM_PROMPT in call["messages"][0]["content"]
    assert call["messages"][-1] == {"role": "user", "content": "I have fever."}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (provider_error(401), AIAuthenticationError),
        (provider_error(429), AIRateLimitError),
        (APITimeoutError(request=None), AITimeoutError),
        (APIConnectionError(request=None), AIConnectionError),
        (provider_error(500), AIUpstreamError),
    ],
)
async def test_provider_errors_are_mapped(exception, expected, monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-key")
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=AsyncMock(side_effect=exception))
        )
    )
    with patch("app.services.ai_service.AsyncOpenAI", return_value=fake_client):
        with pytest.raises(expected):
            await generate_clinical_response([])