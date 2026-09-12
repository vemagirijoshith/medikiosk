from app.models import Consultation, Document, Encounter, OCRResult, PhysicianReviewAudit, Symptom


def _grant(client, patient_id):
    response = client.post(f"/patients/{patient_id}/consents", json={
        "action": "grant", "purpose": "physician_review", "consent_version": "v1",
    })
    assert response.status_code == 201


def _consultation(session_factory, patient_id):
    db = session_factory()
    try:
        encounter = Encounter(patient_id=patient_id, chief_complaint="headache", language="en")
        db.add(encounter)
        db.flush()
        db.add(Symptom(encounter_id=encounter.id, name="headache", description="two days"))
        consultation = Consultation(patient_id=patient_id, encounter_id=encounter.id)
        db.add(consultation)
        db.commit()
        return encounter.id, consultation.id
    finally:
        db.close()


def _document_with_extraction(session_factory, patient_id):
    data = {"patient": {"name": None, "age": None, "sex": None, "patient_id": None},
        "document": {"document_date": "2026-01-01", "document_type": "lab", "hospital": None, "doctor": None},
        "observations": [{"name": "Hemoglobin", "value": "10", "unit": "g/dL", "reference_range": "13-17", "status": None, "source_text": "Hb 10"}],
        "medications": [], "allergies": [], "diagnoses_or_conditions": [], "procedures": [], "clinical_notes": []}
    db = session_factory()
    try:
        document = Document(patient_id=patient_id, file_name="lab.pdf", file_url="local", content_type="application/pdf", file_size=1, document_type="lab", ocr_status="completed")
        db.add(document)
        db.flush()
        result = OCRResult(document_id=document.id, extracted_text="Hb 10", structured_data={"medical_extraction": data})
        db.add(result)
        db.commit()
        return document.id, result.id
    finally:
        db.close()


def test_packet_is_consent_gated_and_preserves_source_ids(client, synthetic_patient):
    test_client, session_factory = client
    encounter_id, _ = _consultation(session_factory, synthetic_patient["id"])
    document_id, ocr_id = _document_with_extraction(session_factory, synthetic_patient["id"])
    assert test_client.get(f"/patients/{synthetic_patient['id']}/physician-review-packet").status_code == 403
    _grant(test_client, synthetic_patient["id"])
    response = test_client.get(f"/patients/{synthetic_patient['id']}/physician-review-packet", params={"encounter_id": encounter_id})
    assert response.status_code == 200
    packet = response.json()
    assert packet["symptoms"][0]["name"] == "headache"
    assert packet["medical_extraction"][0]["source_document_id"] == document_id
    assert packet["medical_extraction"][0]["ocr_result_id"] == ocr_id
    assert packet["medical_extraction"][0]["physician_verified"] is False
    assert packet["clinical_summary"]["physician_verified"] is False


def test_missing_or_unrelated_patient_encounter_is_rejected(client, synthetic_patient):
    test_client, session_factory = client
    encounter_id, _ = _consultation(session_factory, synthetic_patient["id"])
    _grant(test_client, synthetic_patient["id"])
    assert test_client.get("/patients/999999/physician-review-packet").status_code == 404
    second = test_client.post("/patients/", json={"name": "Other", "age": 30, "gender": "unknown"}).json()
    _grant(test_client, second["id"])
    assert test_client.get(f"/patients/{second['id']}/physician-review-packet", params={"encounter_id": encounter_id}).status_code == 404


def test_review_transitions_are_audited_and_do_not_mutate_ocr(client, synthetic_patient):
    test_client, session_factory = client
    _, consultation_id = _consultation(session_factory, synthetic_patient["id"])
    document_id, _ = _document_with_extraction(session_factory, synthetic_patient["id"])
    _grant(test_client, synthetic_patient["id"])
    db = session_factory()
    original = db.query(OCRResult).filter(OCRResult.document_id == document_id).one().structured_data
    db.close()
    notes = test_client.post(f"/patients/{synthetic_patient['id']}/consultations/{consultation_id}/review/notes", json={"physician_id": "external-id", "notes": "Reviewed source."})
    assert notes.json()["review_status"] == "in_review"
    assert notes.json()["physician_id_authenticated"] is False
    invalid = test_client.post(f"/patients/{synthetic_patient['id']}/consultations/{consultation_id}/review/verify", json={"verified_fields": ["diagnoses"]})
    assert invalid.status_code == 422
    verified = test_client.post(f"/patients/{synthetic_patient['id']}/consultations/{consultation_id}/review/verify", json={"verified_fields": ["symptoms", "allergies"]})
    assert verified.json()["review_status"] == "verified"
    completed = test_client.post(f"/patients/{synthetic_patient['id']}/consultations/{consultation_id}/review/complete", json={})
    assert completed.json()["review_status"] == "completed"
    db = session_factory()
    try:
        assert db.query(PhysicianReviewAudit).filter_by(consultation_id=consultation_id).count() == 3
        assert db.query(OCRResult).filter(OCRResult.document_id == document_id).one().structured_data == original
    finally:
        db.close()


def test_completion_requires_verification_and_revoked_consent_is_denied(client, synthetic_patient):
    test_client, session_factory = client
    _, consultation_id = _consultation(session_factory, synthetic_patient["id"])
    _grant(test_client, synthetic_patient["id"])
    complete = test_client.post(f"/patients/{synthetic_patient['id']}/consultations/{consultation_id}/review/complete", json={})
    assert complete.status_code == 409
    consents = test_client.get(f"/patients/{synthetic_patient['id']}/consents").json()["consents"]
    revoked = test_client.post(f"/patients/{synthetic_patient['id']}/consents/{consents[0]['id']}/revoke", json={})
    assert revoked.status_code == 200
    response = test_client.post(f"/patients/{synthetic_patient['id']}/consultations/{consultation_id}/review/notes", json={"notes": "blocked"})
    assert response.status_code == 403
