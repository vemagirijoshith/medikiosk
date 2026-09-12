from datetime import datetime, timezone

from app.api.intake import _conversations
from app.models.consent import Consent, ConsentStatus
from app.models.encounter import Encounter
from app.services.consent_service import has_active_consent


def grant(client, patient_id, purpose, version="v1"):
    return client.post(
        f"/patients/{patient_id}/consents",
        json={
            "action": "grant",
            "purpose": purpose,
            "consent_version": version,
            "source": "synthetic_test",
        },
    )


def test_patient_not_found(client):
    response = grant(client[0], 999999, "clinical_history")
    assert response.status_code == 404


def test_grant_retrieve_and_check_consent(client, synthetic_patient):
    test_client, _ = client
    response = grant(test_client, synthetic_patient["id"], "clinical_history")
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "granted"
    assert payload["metadata"] is None

    listing = test_client.get(f"/patients/{synthetic_patient['id']}/consents")
    assert listing.status_code == 200
    assert len(listing.json()["consents"]) == 1
    check = test_client.get(
        f"/patients/{synthetic_patient['id']}/consents/check",
        params={"purpose": "clinical_history"},
    )
    assert check.status_code == 200
    assert check.json()["has_consent"] is True


def test_purposes_are_independent_and_missing_is_denied(client, synthetic_patient):
    test_client, session_factory = client
    assert grant(test_client, synthetic_patient["id"], "document_processing").status_code == 201
    db = session_factory()
    try:
        assert has_active_consent(db, synthetic_patient["id"], "document_processing") is True
        assert has_active_consent(db, synthetic_patient["id"], "abdm_sharing") is False
    finally:
        db.close()


def test_revoke_preserves_history_and_disables_active_check(client, synthetic_patient):
    test_client, session_factory = client
    created = grant(test_client, synthetic_patient["id"], "physician_review")
    consent_id = created.json()["id"]
    revoked = test_client.post(
        f"/patients/{synthetic_patient['id']}/consents/{consent_id}/revoke",
        json={"reason": "synthetic withdrawal"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert revoked.json()["revoked_at"] is not None
    db = session_factory()
    try:
        assert has_active_consent(db, synthetic_patient["id"], "physician_review") is False
        assert db.query(Consent).filter_by(id=consent_id).count() == 1
    finally:
        db.close()


def test_repeated_grant_revokes_previous_record(client, synthetic_patient):
    test_client, session_factory = client
    first = grant(test_client, synthetic_patient["id"], "clinical_summary", "v1").json()
    second = grant(test_client, synthetic_patient["id"], "clinical_summary", "v2").json()
    assert first["id"] != second["id"]
    listing = test_client.get(f"/patients/{synthetic_patient['id']}/consents").json()["consents"]
    assert len(listing) == 2
    assert {item["status"] for item in listing} == {"granted", "revoked"}
    db = session_factory()
    try:
        assert has_active_consent(db, synthetic_patient["id"], "clinical_summary") is True
    finally:
        db.close()


def test_expired_consent_does_not_pass(client, synthetic_patient):
    test_client, session_factory = client
    created = grant(test_client, synthetic_patient["id"], "document_extraction").json()
    db = session_factory()
    try:
        consent = db.get(Consent, created["id"])
        consent.status = ConsentStatus.EXPIRED.value
        consent.granted = False
        db.commit()
        assert has_active_consent(db, synthetic_patient["id"], "document_extraction") is False
    finally:
        db.close()


def test_terminate_session_invalidates_messages(client, synthetic_patient):
    test_client, session_factory = client
    db = session_factory()
    encounter = Encounter(patient_id=synthetic_patient["id"], language="en", status="collecting")
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    encounter_id = encounter.id
    db.close()
    _conversations[encounter_id] = [{"role": "user", "content": "synthetic"}]

    response = test_client.post(f"/intake/{encounter_id}/terminate")
    assert response.status_code == 204
    assert encounter_id not in _conversations
    follow_up = test_client.post(
        "/intake/message",
        json={"encounter_id": encounter_id, "message": "hello"},
    )
    assert follow_up.status_code == 409
