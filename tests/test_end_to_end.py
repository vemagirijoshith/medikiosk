"""Offline E1 integration coverage using only synthetic data and service-boundary mocks."""
import json
from copy import deepcopy
from unittest.mock import AsyncMock, patch

from app.api import documents as documents_api
from app.models import ABDMShareAudit, Consultation, Document, OCRResult, PhysicianReviewAudit, Symptom
from app.schemas.clinical_summary import ClinicalSummary


OCR_TEXT = "Hemoglobin: 12.5 g/dL\nBlood pressure: 120/80 mmHg\nSynthetic medication: ExampleMed 10 mg daily"

EXTRACTION = {
    "patient": {"name": None, "age": None, "sex": None, "patient_id": None},
    "document": {"document_date": "2026-09-01", "document_type": "synthetic_lab", "hospital": None, "doctor": None},
    "observations": [
        {"name": "Hemoglobin", "value": "12.5", "unit": "g/dL", "reference_range": "12.0-16.0", "status": None, "source_text": "Hemoglobin: 12.5 g/dL"},
        {"name": "Blood pressure", "value": "120/80", "unit": "mmHg", "reference_range": None, "status": None, "source_text": "Blood pressure: 120/80 mmHg"},
    ],
    "medications": [{"name": "ExampleMed", "dose": "10 mg", "frequency": "daily", "route": None, "duration": None, "source_text": "Synthetic medication: ExampleMed 10 mg daily"}],
    "allergies": [], "diagnoses_or_conditions": [], "procedures": [], "clinical_notes": [],
}


def _grant_all(client, patient_id):
    records = {}
    for purpose in ("clinical_history", "document_processing", "document_extraction", "clinical_summary", "abdm_sharing", "physician_review"):
        response = client.post(f"/patients/{patient_id}/consents", json={"action": "grant", "purpose": purpose, "consent_version": "e1-v1", "source": "synthetic_e1"})
        assert response.status_code == 201
        records[purpose] = response.json()
    return records


def _summary(patient_id, encounter_id, document_id):
    return ClinicalSummary.model_validate({
        "patient": {"name": "E2E Test Patient", "age": "38", "sex": "unknown", "patient_id": str(patient_id)},
        "encounter": {"encounter_id": encounter_id, "chief_complaint": "headache", "encounter_date": None},
        "history_of_present_illness": "Synthetic patient-reported headache for two days.",
        "symptoms": [{"name": "headache", "details": "two days", "source": "patient_history"}],
        "medications": [], "allergies": [],
        "relevant_document_findings": [{"document_id": document_id, "date": "2026-09-01", "finding": "Hemoglobin recorded in source document.", "source_text": "Hemoglobin: 12.5 g/dL"}],
        "observations": [{"document_id": document_id, "name": "Hemoglobin", "value": "12.5", "unit": "g/dL", "reference_range": "12.0-16.0", "status": "normal", "source_text": "Hemoglobin: 12.5 g/dL"}],
        "timeline": [{"date": "2026-09-01", "event": "Synthetic lab document", "source": "document"}],
        "red_flags": [], "diagnoses_or_conditions": [],
        "summary": "Synthetic structured history for physician review; not physician verified.",
    })


def test_complete_offline_synthetic_workflow(client, tmp_path):
    test_client, session_factory = client
    patient = test_client.post("/patients/", json={"name": "E2E Test Patient", "age": 38, "gender": "unknown", "language": "en"}).json()
    patient_id = patient["id"]
    consents = _grant_all(test_client, patient_id)

    started = test_client.post("/intake/start", json={"patient_id": patient_id, "language": "en", "mode": "general"})
    assert started.status_code == 201
    encounter_id = started.json()["encounter_id"]
    first_intake_output = json.dumps({"assistant_message": "Please describe the duration.", "status": "collecting", "clinical_data": {"chief_complaint": "headache", "duration": "two days", "severity": "mild", "character": "synthetic intermittent pain"}, "red_flags": []})
    final_intake_output = json.dumps({"assistant_message": "Thank you; your history is ready for review.", "status": "ready_for_review", "clinical_data": {}, "red_flags": []})
    with patch("app.api.intake.generate_clinical_response", new=AsyncMock(side_effect=[first_intake_output, final_intake_output])):
        collecting = test_client.post("/intake/message", json={"encounter_id": encounter_id, "message": "Synthetic headache for two days, mild."})
        assert collecting.status_code == 200 and collecting.json()["status"] == "collecting"
        intake = test_client.post("/intake/message", json={"encounter_id": encounter_id, "message": "No other synthetic symptoms."})
    assert intake.status_code == 200 and intake.json()["status"] == "ready_for_review"

    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        upload = test_client.post("/documents/upload", data={"patient_id": str(patient_id), "encounter_id": str(encounter_id)}, files={"file": ("synthetic-lab.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")})
        assert upload.status_code == 201
        document_id = upload.json()["id"]
        assert upload.json()["filename"] == "synthetic-lab.png"
        with patch("app.api.documents.extract_document_text", new=AsyncMock(return_value={"text": OCR_TEXT, "pages": [], "elements": [], "tables": [], "confidence": None, "raw_response": []})):
            ocr = test_client.post(f"/documents/{document_id}/ocr")
    assert ocr.status_code == 200 and ocr.json()["status"] == "completed"
    ocr_id = ocr.json()["structured_data"]  # confirms data came through the actual OCR route
    assert ocr.json()["extracted_text"] == OCR_TEXT and ocr_id["text"] == OCR_TEXT

    with patch("app.api.documents.generate_medical_extraction", new=AsyncMock(return_value=json.dumps(EXTRACTION))):
        extracted = test_client.post(f"/documents/{document_id}/extract")
    assert extracted.status_code == 200
    assert extracted.json()["extraction"]["observations"][0]["source_text"] == "Hemoglobin: 12.5 g/dL"
    intelligence = test_client.get(f"/documents/{document_id}/intelligence")
    assert intelligence.status_code == 200
    assert intelligence.json()["highlighted_observations"][0]["status"] == "normal"
    assert intelligence.json()["highlighted_observations"][0]["document_id"] == document_id
    assert intelligence.json()["highlighted_observations"][1]["status"] == "unknown"

    summary_value = _summary(patient_id, encounter_id, document_id)
    with patch("app.api.clinical_summary.generate_clinical_summary", new=AsyncMock(return_value=summary_value)):
        summary = test_client.get(f"/patients/{patient_id}/clinical-summary", params={"encounter_id": encounter_id})
    assert summary.status_code == 200
    assert summary.json()["generated_summary"]["observations"][0]["document_id"] == document_id
    assert summary.json()["generated_summary"]["red_flags"] == []

    assert test_client.put(f"/patients/{patient_id}/abha", json={"abha_id": "12345678901234"}).status_code == 200
    export = test_client.post(f"/patients/{patient_id}/abdm/export", json={"encounter_id": encounter_id})
    assert export.status_code == 200
    assert export.json()["status"] == "sandbox_ready"
    assert export.json()["payload"]["provenance"]["document_ids"] == [document_id]
    assert "secret" not in json.dumps(export.json()).lower()

    db = session_factory()
    try:
        consultation = Consultation(patient_id=patient_id, encounter_id=encounter_id)
        db.add(consultation)
        db.commit()
        consultation_id = consultation.id
        original_ocr = deepcopy(db.query(OCRResult).filter_by(document_id=document_id).one().structured_data)
    finally:
        db.close()
    packet = test_client.get(f"/patients/{patient_id}/physician-review-packet", params={"encounter_id": encounter_id})
    assert packet.status_code == 200
    packet_data = packet.json()
    assert packet_data["patient"]["patient_id"] == patient_id
    assert packet_data["encounter"]["encounter_id"] == encounter_id
    assert packet_data["symptoms"][0]["name"] == "headache"
    assert packet_data["documents"][0]["document_id"] == document_id
    assert packet_data["ocr_findings"][0]["source_document_id"] == document_id
    assert packet_data["medical_extraction"][0]["source_document_id"] == document_id
    assert packet_data["document_intelligence"][0]["observations"][0]["status"] == "normal"
    # Summaries are transient in the current production design; packet explicitly does not regenerate AI output.
    assert packet_data["clinical_summary"]["available"] is False
    assert packet_data["medical_extraction"][0]["physician_verified"] is False

    assert test_client.post(f"/patients/{patient_id}/consultations/{consultation_id}/review/notes", json={"physician_id": "synthetic-external-id", "notes": "Synthetic source review completed."}).json()["review_status"] == "in_review"
    assert test_client.post(f"/patients/{patient_id}/consultations/{consultation_id}/review/verify", json={"physician_id": "synthetic-external-id", "verified_fields": ["symptoms", "allergies"]}).json()["review_status"] == "verified"
    assert test_client.post(f"/patients/{patient_id}/consultations/{consultation_id}/review/complete", json={"physician_id": "synthetic-external-id"}).json()["review_status"] == "completed"

    db = session_factory()
    try:
        assert db.query(Symptom).filter_by(encounter_id=encounter_id).count() == 1
        assert db.get(Document, document_id).file_name == "synthetic-lab.png"
        assert db.query(OCRResult).filter_by(document_id=document_id).one().structured_data == original_ocr
        assert db.query(ABDMShareAudit).filter_by(patient_id=patient_id, action="sandbox_export_prepared").count() == 1
        assert db.query(PhysicianReviewAudit).filter_by(consultation_id=consultation_id).count() == 3
    finally:
        db.close()

    revoked = test_client.post(f"/patients/{patient_id}/consents/{consents['abdm_sharing']['id']}/revoke", json={})
    assert revoked.status_code == 200
    assert test_client.post(f"/patients/{patient_id}/abdm/export", json={"encounter_id": encounter_id}).status_code == 403
    physician_revoked = test_client.post(f"/patients/{patient_id}/consents/{consents['physician_review']['id']}/revoke", json={})
    assert physician_revoked.status_code == 200
    assert test_client.get(f"/patients/{patient_id}/physician-review-packet").status_code == 403
