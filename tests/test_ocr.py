from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from app.api import documents as documents_api
from app.models import Document, OCRResult
from app.services import ocr_service
from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)


PNG = b"\x89PNG\r\n\x1a\nsynthetic image"


def upload(client, patient_id, content=PNG, filename="scan.png", content_type="image/png"):
    return client.post(
        "/documents/upload",
        data={"patient_id": str(patient_id)},
        files={"file": (filename, content, content_type)},
    )


def ocr_response(text="Extracted synthetic text"):
    return {"data": [{"index": 0, "text_detections": [{"text": text}]}], "usage": {}}


class FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload

    @classmethod
    def with_status(cls, status_code):
        response = cls({})
        response.status_code = status_code
        return response

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return self.response


@pytest.mark.asyncio
async def test_ocr_service_uses_nim_ocr_contract_for_image(tmp_path, monkeypatch):
    path = tmp_path / "scan.png"
    path.write_bytes(PNG)
    fake_client = FakeAsyncClient(FakeResponse(ocr_response()))
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("NVIDIA_OCR_BASE_URL", "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2")
    monkeypatch.setenv("NVIDIA_OCR_MODEL", "nvidia/nemotron-ocr-v2")

    with patch("app.services.ocr_service.httpx.AsyncClient", return_value=fake_client):
        result = await ocr_service.extract_document_text(path, "image/png")

    assert result["text"] == "Extracted synthetic text"
    url, request = fake_client.requests[0]
    assert url == "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2"
    assert "model" not in request["json"]
    assert request["json"]["input"][0]["type"] == "image_url"
    assert request["json"]["input"][0]["url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_pdf_is_rendered_to_image_pages(tmp_path, monkeypatch):
    path = tmp_path / "record.pdf"
    path.write_bytes(b"%PDF-synthetic")
    fake_client = FakeAsyncClient(FakeResponse(ocr_response("PDF page text")))
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-key")
    with patch("app.services.ocr_service._render_pdf_pages", return_value=[(PNG, "image/png")]) as render:
        with patch("app.services.ocr_service.httpx.AsyncClient", return_value=fake_client):
            result = await ocr_service.extract_document_text(path, "application/pdf")
    render.assert_called_once_with(path)
    assert result["text"] == "PDF page text"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (FakeResponse.with_status(401), AIAuthenticationError),
        (FakeResponse.with_status(429), AIRateLimitError),
        (httpx.ReadTimeout("timeout"), AITimeoutError),
        (httpx.ConnectError("connection"), AIConnectionError),
        (FakeResponse.with_status(500), AIUpstreamError),
    ],
)
async def test_ocr_provider_errors_are_normalized(tmp_path, monkeypatch, exception, expected):
    path = tmp_path / "scan.png"
    path.write_bytes(PNG)
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-key")
    fake_client = FakeAsyncClient(exception if isinstance(exception, FakeResponse) else None)
    if not isinstance(exception, FakeResponse):
        fake_client.post = AsyncMock(side_effect=exception)
    with patch("app.services.ocr_service.httpx.AsyncClient", return_value=fake_client):
        with pytest.raises(expected):
            await ocr_service.extract_document_text(path, "image/png")


def test_ocr_endpoint_persists_result_and_status(client, synthetic_patient, tmp_path):
    test_client, session_factory = client
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        uploaded = upload(test_client, synthetic_patient["id"])
    document_id = uploaded.json()["id"]
    stored_path = next(tmp_path.iterdir())
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path), patch(
        "app.api.documents.extract_document_text",
        new=AsyncMock(return_value={"text": "OCR text", "pages": [], "elements": [], "tables": [], "confidence": None, "raw_response": []}),
    ):
        response = test_client.post(f"/documents/{document_id}/ocr")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    db = session_factory()
    try:
        document = db.get(Document, document_id)
        result = db.query(OCRResult).filter_by(document_id=document_id).one()
        assert document.ocr_status == "completed"
        assert result.extracted_text == "OCR text"
    finally:
        db.close()
    assert stored_path.exists()


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(FileNotFoundError(), 404), (AIAuthenticationError(), 502), (AIRateLimitError(), 503), (AITimeoutError(), 504), (AIConnectionError(), 503), (AIUpstreamError(), 502)],
)
def test_ocr_endpoint_errors_mark_document_failed(client, synthetic_patient, tmp_path, error, status_code):
    test_client, session_factory = client
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        uploaded = upload(test_client, synthetic_patient["id"])
    document_id = uploaded.json()["id"]
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path), patch(
        "app.api.documents.extract_document_text", new=AsyncMock(side_effect=error)
    ):
        response = test_client.post(f"/documents/{document_id}/ocr")
    assert response.status_code == status_code
    db = session_factory()
    try:
        assert db.get(Document, document_id).ocr_status == "failed"
    finally:
        db.close()


def test_ocr_endpoint_missing_document_and_file(client):
    test_client, _ = client
    assert test_client.post("/documents/999999/ocr").status_code == 404
