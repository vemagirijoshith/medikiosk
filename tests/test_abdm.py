from app.models import ABDMShareAudit, Consent, Encounter
from app.services.consent_service import has_active_consent


def grant_abdm(client, patient_id):
    return client.post(
        f"/patients/{patient_id}/consents",
        json={
            "action": "grant",
            "purpose": "abdm_sharing",
            "consent_version": "d2-v1",
            "source": "synthetic_test",
        },
    )


def link_abha(client, patient_id, value="12345678901234"):
    return client.put(f"/patients/{patient_id}/abha", json={"abha_id": value})


def test_abha_link_succeeds_for_existing_patient(client, synthetic_patient):
    response = link_abha(client[0], synthetic_patient["id"])
    assert response.status_code == 200
    assert response.json() == {
        "patient_id": synthetic_patient["id"],
        "abha_id": "12345678901234",
        "status": "linked",
        "verified": False,
    }


def test_abha_link_missing_patient_and_invalid_identifier(client):
    test_client, _ = client
    assert link_abha(test_client, 999999).status_code == 404
    assert link_abha(test_client, 999999, "bad").status_code == 404


def test_abha_invalid_request_returns_422(client, synthetic_patient):
    assert link_abha(client[0], synthetic_patient["id"], "bad").status_code == 422
    assert link_abha(client[0], synthetic_patient["id"], "123456789012345").status_code == 422


def test_duplicate_abha_is_rejected_safely(client):
    test_client, session_factory = client
    first = test_client.post(
        "/patients/", json={"name": "First Synthetic", "age": 30, "gender": "unknown", "language": "en"}
    ).json()
    second = test_client.post(
        "/patients/", json={"name": "Second Synthetic", "age": 31, "gender": "unknown", "language": "en"}
    ).json()
    assert link_abha(test_client, first["id"]).status_code == 200
    duplicate = link_abha(test_client, second["id"])
    assert duplicate.status_code == 422
    db = session_factory()
    try:
        assert db.get(__import__("app.models", fromlist=["Patient"]).Patient, second["id"]).abha_id is None
    finally:
        db.close()


def create_encounter(session_factory, patient_id):
    db = session_factory()
    encounter = Encounter(patient_id=patient_id, language="en", status="collecting", chief_complaint="synthetic complaint")
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    encounter_id = encounter.id
    db.close()
    return encounter_id


def test_export_requires_consent_and_records_blocked_audit(client, synthetic_patient):
    test_client, session_factory = client
    link_abha(test_client, synthetic_patient["id"])
    response = test_client.post(f"/patients/{synthetic_patient['id']}/abdm/export", json={})
    assert response.status_code == 403
    db = session_factory()
    try:
        audit = db.query(ABDMShareAudit).filter_by(patient_id=synthetic_patient["id"]).one()
        assert audit.action == "export_blocked_no_consent"
        assert audit.status == "blocked"
    finally:
        db.close()


def test_sandbox_export_uses_active_consent_and_source_data(client, synthetic_patient):
    test_client, session_factory = client
    link_abha(test_client, synthetic_patient["id"])
    consent = grant_abdm(test_client, synthetic_patient["id"])
    assert consent.status_code == 201
    encounter_id = create_encounter(session_factory, synthetic_patient["id"])
    response = test_client.post(
        f"/patients/{synthetic_patient['id']}/abdm/export",
        json={"encounter_id": encounter_id},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "sandbox_ready"
    assert payload["abha_id"] == "12345678901234"
    assert payload["payload"]["patient"]["name"] == "Synthetic Test Patient"
    assert payload["payload"]["provenance"]["encounter_ids"] == [encounter_id]
    assert "client_secret" not in str(payload).lower()
    db = session_factory()
    try:
        audit = db.query(ABDMShareAudit).filter_by(patient_id=synthetic_patient["id"], action="sandbox_export_prepared").one()
        assert audit.consent_id == consent.json()["id"]
    finally:
        db.close()


def test_export_wrong_encounter_is_rejected(client, synthetic_patient):
    test_client, session_factory = client
    other = test_client.post(
        "/patients/", json={"name": "Other Synthetic", "age": 33, "gender": "unknown", "language": "en"}
    ).json()
    encounter_id = create_encounter(session_factory, other["id"])
    link_abha(test_client, synthetic_patient["id"])
    grant_abdm(test_client, synthetic_patient["id"])
    assert test_client.post(
        f"/patients/{synthetic_patient['id']}/abdm/export", json={"encounter_id": encounter_id}
    ).status_code == 404


def test_revoked_and_expired_consent_block_export(client, synthetic_patient):
    test_client, session_factory = client
    link_abha(test_client, synthetic_patient["id"])
    consent = grant_abdm(test_client, synthetic_patient["id"]).json()
    test_client.post(f"/patients/{synthetic_patient['id']}/consents/{consent['id']}/revoke", json={})
    assert test_client.post(f"/patients/{synthetic_patient['id']}/abdm/export", json={}).status_code == 403
    fresh = grant_abdm(test_client, synthetic_patient["id"]).json()
    db = session_factory()
    try:
        record = db.get(Consent, fresh["id"])
        record.status = "expired"
        record.granted = False
        db.commit()
    finally:
        db.close()
    assert test_client.post(f"/patients/{synthetic_patient['id']}/abdm/export", json={}).status_code == 403
    db = session_factory()
    try:
        assert has_active_consent(db, synthetic_patient["id"], "abdm_sharing") is False
    finally:
        db.close()