import pytest
from app.api.intake import _red_flags_for_message
from app.models.consultation import Consultation
from app.models.encounter import Encounter
from app.models.patient import Patient


def test_red_flag_triggers():
    """Verify high-sensitivity emergency red-flag triggers."""
    assert len(_red_flags_for_message("I have severe crushing chest pain")) > 0
    assert len(_red_flags_for_message("I am feeling extreme shortness of breath and cannot breathe")) > 0
    assert len(_red_flags_for_message("Heavy active bleeding from deep wound")) > 0
    assert len(_red_flags_for_message("Patient had loss of consciousness and fainted")) > 0
    assert len(_red_flags_for_message("I have mild cold and sneezing")) == 0


def test_monotonic_queue_priority_escalation(client, synthetic_patient):
    test_client, session_maker = client
    patient_id = synthetic_patient["id"]

    # Start an intake encounter
    # Grant clinical history consent first
    test_client.post(
        f"/patients/{patient_id}/consents",
        json={
            "action": "grant",
            "purpose": "clinical_history",
            "consent_version": "kiosk-v1",
            "source": "test",
        },
    )

    start_res = test_client.post(
        "/intake/start",
        json={"patient_id": patient_id, "language": "en", "mode": "general"},
    )
    assert start_res.status_code == 201
    encounter_id = start_res.json()["encounter_id"]

    # Send an urgent red-flag message (chest pain)
    msg_res = test_client.post(
        "/intake/message",
        json={"encounter_id": encounter_id, "message": "I am experiencing acute severe chest pain radiating to left arm"},
    )
    assert msg_res.status_code == 200
    assert msg_res.json()["status"] == "needs_staff_attention"
    assert len(msg_res.json()["red_flags"]) > 0

    # Verify encounter in database is now urgent
    with session_maker() as db:
        enc = db.get(Encounter, encounter_id)
        assert enc.priority == "urgent"
        assert enc.red_flag_reason is not None

    # Verify that creating a consultation for this encounter inherits urgent priority
    consult_res = test_client.post(
        f"/patients/{patient_id}/consultations",
        json={"encounter_id": encounter_id},
    )
    assert consult_res.status_code == 201
    assert consult_res.json()["priority"] == "urgent"
    assert "chest" in consult_res.json()["red_flag_reason"].lower()


def test_physician_queue_sorting_prioritizes_urgent(client):
    """Urgent consultations must be sorted ahead of routine consultations."""
    test_client, session_maker = client

    with session_maker() as db:
        # Create routine patient 1 first (earlier timestamp)
        p1 = Patient(name="Routine Patient", age=30, gender="male", language="en")
        db.add(p1)
        db.commit()
        db.refresh(p1)

        e1 = Encounter(patient_id=p1.id, priority="routine", chief_complaint="routine checkup")
        db.add(e1)
        db.commit()
        db.refresh(e1)

        c1 = Consultation(patient_id=p1.id, encounter_id=e1.id, priority="routine", review_status="pending")
        db.add(c1)
        db.commit()

        # Create urgent patient 2 later
        p2 = Patient(name="Urgent Emergency Patient", age=55, gender="female", language="en")
        db.add(p2)
        db.commit()
        db.refresh(p2)

        e2 = Encounter(patient_id=p2.id, priority="urgent", red_flag_reason="chest pain", chief_complaint="acute chest pain")
        db.add(e2)
        db.commit()
        db.refresh(e2)

        c2 = Consultation(patient_id=p2.id, encounter_id=e2.id, priority="urgent", red_flag_reason="chest pain", review_status="pending")
        db.add(c2)
        db.commit()

    resp = test_client.get("/patients/physician/reviews")
    assert resp.status_code == 200
    queue = resp.json()
    assert len(queue) >= 2

    # The first item in the queue MUST be the urgent patient
    assert queue[0]["priority"] == "urgent"
    assert queue[0]["patient_name"] == "Urgent Emergency Patient"
    assert queue[0]["red_flag_reason"] == "chest pain"
