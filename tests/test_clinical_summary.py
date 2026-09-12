import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.models import Allergy, Encounter, Medication, OCRResult, Symptom
from app.services.ai_service import AIAuthenticationError, AITimeoutError, AIUpstreamError
from app.services.clinical_summary_service import generate_clinical_summary


def valid_summary():
    return {
        "patient": {"name": "Synthetic Patient", "age": "45", "sex": "Male", "patient_id": "1"},
        "encounter": {"encounter_id": 1, "chief_complaint": "headache", "encounter_date": None},
        "history_of_present_illness": "Patient reports headache.",
        "symptoms": [{"name": "headache", "details": "two days", "source": "patient_history"}],
        "medications": [{"name": "Metformin", "dose": "500 mg", "frequency": "twice daily", "source": "patient_history"}],
        "allergies": [{"substance": "Penicillin", "reaction": "rash", "source": "patient_history"}],
        "relevant_document_findings": [],
        "observations": [],
        "timeline": [{"date": None, "event": "Headache reported", "source": "patient_history"}],
        "red_flags": [],
        "diagnoses_or_conditions": [],
        "summary": "Patient reports headache for two days. Medication and allergy information are listed for review.",
    }


def completion(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def seed_encounter(client, session_factory, patient_id):
    db = session_factory()
    encounter = Encounter(patient_id=patient_id, chief_complaint="headache", language="en", status="collecting")
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    db.add(Symptom(encounter_id=encounter.id, name="headache", duration="two days", description="patient reported"))
    db.add(Medication(patient_id=patient_id, name="Metformin", dosage="500 mg", frequency="twice daily", source="patient_history"))
    db.add(Allergy(patient_id=patient_id, allergen="Penicillin", reaction="rash"))
    db.commit()
    encounter_id = encounter.id
    db.close()
    return encounter_id


def test_summary_endpoint_success_and_source_facts_unchanged(client, synthetic_patient):
    test_client, session_factory = client
    encounter_id = seed_encounter(test_client, session_factory, synthetic_patient["id"])
    with patch("app.api.clinical_summary.generate_clinical_summary", new=AsyncMock(return_value=__import__("app.schemas.clinical_summary", fromlist=["ClinicalSummary"]).ClinicalSummary.model_validate(valid_summary()))):
        response = test_client.get(f"/patients/{synthetic_patient['id']}/clinical-summary?encounter_id={encounter_id}")
    assert response.status_code == 200
    assert response.json()["generated_summary"]["medications"][0]["name"] == "Metformin"
    db = session_factory()
    try:
        assert db.query(Symptom).filter_by(encounter_id=encounter_id).count() == 1
        assert db.query(Medication).filter_by(patient_id=synthetic_patient["id"]).count() == 1
    finally:
        db.close()


def test_summary_patient_and_encounter_not_found(client):
    test_client, _ = client
    assert test_client.get("/patients/999999/clinical-summary").status_code == 404


def test_summary_missing_encounter(client, synthetic_patient):
    assert client[0].get(f"/patients/{synthetic_patient['id']}/clinical-summary").status_code == 404


def test_summary_rejects_unsupported_medication_and_diagnosis():
    from app.services.clinical_summary_service import _check_supported

    source = {"medications": [{"name": "Metformin"}], "allergies": [], "diagnoses_or_conditions": [], "document_ids": [], "document_dates": []}
    summary = valid_summary()
    summary["medications"][0]["name"] = "Insulin"
    from app.schemas.clinical_summary import ClinicalSummary
    with pytest.raises(ValueError):
        _check_supported(ClinicalSummary.model_validate(summary), source)
    summary = valid_summary()
    summary["diagnoses_or_conditions"] = ["diabetes"]
    with pytest.raises(ValueError):
        _check_supported(ClinicalSummary.model_validate(summary), source)


@pytest.mark.asyncio
async def test_summary_service_uses_existing_nemotron_configuration(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "synthetic-key")
    fake_create = AsyncMock(return_value=completion(json.dumps(valid_summary())))
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))
    source = {"medications": [{"name": "Metformin"}], "allergies": [{"substance": "Penicillin"}], "diagnoses_or_conditions": [], "document_ids": [], "document_dates": []}
    with patch("app.services.clinical_summary_service.AsyncOpenAI", return_value=fake_client) as client_class:
        result = await generate_clinical_summary(source)
    assert result.summary.startswith("Patient reports")
    client_class.assert_called_once_with(
        api_key="synthetic-key",
        base_url="https://integrate.api.nvidia.com/v1",
        timeout=30.0,
        max_retries=0,
    )
    assert "Use ONLY the supplied information" in fake_create.await_args.kwargs["messages"][0]["content"]


@pytest.mark.parametrize("raw", ["not json", "```json\n{}\n```"])
def test_summary_malformed_response_returns_422(client, synthetic_patient, raw):
    test_client, session_factory = client
    encounter_id = seed_encounter(test_client, session_factory, synthetic_patient["id"])
    with patch("app.api.clinical_summary.generate_clinical_summary", new=AsyncMock(side_effect=ValueError("bad"))):
        response = test_client.get(f"/patients/{synthetic_patient['id']}/clinical-summary?encounter_id={encounter_id}")
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(AIAuthenticationError(), 503), (AITimeoutError(), 504), (AIUpstreamError(), 502)],
)
def test_summary_provider_errors_are_safe(client, synthetic_patient, error, status_code):
    test_client, session_factory = client
    encounter_id = seed_encounter(test_client, session_factory, synthetic_patient["id"])
    with patch("app.api.clinical_summary.generate_clinical_summary", new=AsyncMock(side_effect=error)):
        response = test_client.get(f"/patients/{synthetic_patient['id']}/clinical-summary?encounter_id={encounter_id}")
    assert response.status_code == status_code
    assert "NVIDIA_API_KEY" not in response.text