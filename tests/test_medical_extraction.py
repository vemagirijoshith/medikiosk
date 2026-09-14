import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.models import OCRResult
from app.services.ai_service import (
    AIAuthenticationError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)
from app.services.medical_extraction_service import (
    EXTRACTION_SYSTEM_PROMPT,
    generate_medical_extraction,
)


OCR_TEXT = """Patient Name: Ravi Kumar
Age: 45
Sex: Male
Hemoglobin: 10.2 g/dL
Metformin 500 mg twice daily
Penicillin - rash"""

VALID_EXTRACTION = {
    "patient": {"name": "Ravi Kumar", "age": "45", "sex": "Male", "patient_id": None},
    "document": {"document_date": None, "document_type": None, "hospital": None, "doctor": None},
    "observations": [{"name": "Hemoglobin", "value": "10.2", "unit": "g/dL", "reference_range": None, "status": None, "source_text": "Hemoglobin: 10.2 g/dL"}],
    "medications": [{"name": "Metformin", "dose": "500 mg", "frequency": "twice daily", "route": None, "duration": None, "source_text": "Metformin 500 mg twice daily"}],
    "allergies": [{"substance": "Penicillin", "reaction": "rash", "source_text": "Penicillin - rash"}],
    "diagnoses_or_conditions": [],
    "procedures": [],
    "clinical_notes": [],
}


def completion(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


@pytest.mark.asyncio
async def test_extraction_service_uses_nvidia_chat_configuration(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
    fake_create = AsyncMock(return_value=completion('{"patient":{}}'))
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))
    with patch("app.services.medical_extraction_service.AsyncOpenAI", return_value=fake_client) as client_class:
        result = await generate_medical_extraction(OCR_TEXT)
    assert result == '{"patient":{}}'
    client_class.assert_called_once()
    request = fake_create.await_args.kwargs
    assert request["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert request["temperature"] == 0
    assert EXTRACTION_SYSTEM_PROMPT in request["messages"][0]["content"]
    assert "Extract ONLY information explicitly present" in request["messages"][0]["content"]
    assert "Never guess" in request["messages"][0]["content"]
    assert "do not diagnose" in request["messages"][0]["content"]
    assert OCR_TEXT in request["messages"][1]["content"]


def upload_and_add_ocr(client, session_factory, patient_id, structured_data=None, text=OCR_TEXT):
    uploaded = client.post(
        "/documents/upload",
        data={"patient_id": str(patient_id)},
        files={"file": ("record.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    document_id = uploaded.json()["id"]
    db = session_factory()
    result = OCRResult(document_id=document_id, extracted_text=text, structured_data=structured_data or {"pages": []})
    db.add(result)
    db.commit()
    db.refresh(result)
    result_id = result.id
    db.close()
    return document_id, result_id


def test_successful_extraction_preserves_ocr_and_is_idempotent(client, synthetic_patient):
    test_client, session_factory = client
    document_id, result_id = upload_and_add_ocr(test_client, session_factory, synthetic_patient["id"], {"pages": [{"text": OCR_TEXT}]})
    with patch("app.api.documents.generate_medical_extraction", new=AsyncMock(return_value=json.dumps(VALID_EXTRACTION))):
        first = test_client.post(f"/documents/{document_id}/extract")
        second = test_client.post(f"/documents/{document_id}/extract")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["extraction"]["observations"][0]["source_text"] == "Hemoglobin: 10.2 g/dL"
    db = session_factory()
    try:
        results = db.query(OCRResult).filter_by(document_id=document_id).all()
        stored = db.get(OCRResult, result_id)
        assert len(results) == 1
        assert stored.structured_data["pages"][0]["text"] == OCR_TEXT
        assert stored.structured_data["medical_extraction"]["patient"]["name"] == "Ravi Kumar"
    finally:
        db.close()


def test_extraction_requires_document_and_ocr_text(client, synthetic_patient):
    test_client, session_factory = client
    assert test_client.post("/documents/999999/extract").status_code == 404
    uploaded = test_client.post(
        "/documents/upload", data={"patient_id": str(synthetic_patient["id"])},
        files={"file": ("record.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    db = session_factory()
    db.add(OCRResult(document_id=uploaded.json()["id"], extracted_text=None, structured_data={"pages": []}))
    db.commit()
    db.close()
    assert test_client.post(f"/documents/{uploaded.json()['id']}/extract").status_code == 422


@pytest.mark.parametrize("raw", ["not json", "```json\n{}\n```", '{"patient": {}}'])
def test_malformed_or_incomplete_extraction_returns_422(client, synthetic_patient, raw):
    test_client, session_factory = client
    document_id, _ = upload_and_add_ocr(test_client, session_factory, synthetic_patient["id"])
    with patch("app.api.documents.generate_medical_extraction", new=AsyncMock(return_value=raw)):
        response = test_client.post(f"/documents/{document_id}/extract")
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(AIAuthenticationError(), 503), (AIRateLimitError(), 503), (AITimeoutError(), 504), (AIUpstreamError(), 502)],
)
def test_extraction_provider_errors_are_safe(client, synthetic_patient, error, status_code):
    test_client, session_factory = client
    document_id, _ = upload_and_add_ocr(test_client, session_factory, synthetic_patient["id"])
    with patch("app.api.documents.generate_medical_extraction", new=AsyncMock(side_effect=error)):
        response = test_client.post(f"/documents/{document_id}/extract")
    assert response.status_code == status_code
    assert "NVIDIA_API_KEY" not in response.text