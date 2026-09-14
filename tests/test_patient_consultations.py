from app.models import Encounter


def test_create_consultation_is_idempotent_and_appears_in_review_queue(client, synthetic_patient):
    test_client, session_factory = client
    db = session_factory()
    try:
        encounter = Encounter(patient_id=synthetic_patient["id"], language="en")
        db.add(encounter)
        db.commit()
        db.refresh(encounter)
        encounter_id = encounter.id
    finally:
        db.close()

    first = test_client.post(
        f"/patients/{synthetic_patient['id']}/consultations",
        json={"encounter_id": encounter_id},
    )
    second = test_client.post(
        f"/patients/{synthetic_patient['id']}/consultations",
        json={"encounter_id": encounter_id},
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["review_status"] == "pending"

    queue = test_client.get("/patients/physician/reviews")
    assert queue.status_code == 200
    assert queue.json()[0]["patient_id"] == synthetic_patient["id"]
    assert queue.json()[0]["encounter_id"] == encounter_id


def test_consultation_rejects_another_patients_encounter(client, synthetic_patient):
    test_client, session_factory = client
    other = test_client.post(
        "/patients/", json={"name": "Other Patient", "age": 36, "gender": "unknown"}
    ).json()
    db = session_factory()
    try:
        encounter = Encounter(patient_id=other["id"], language="en")
        db.add(encounter)
        db.commit()
        db.refresh(encounter)
        encounter_id = encounter.id
    finally:
        db.close()

    response = test_client.post(
        f"/patients/{synthetic_patient['id']}/consultations",
        json={"encounter_id": encounter_id},
    )
    assert response.status_code == 404
