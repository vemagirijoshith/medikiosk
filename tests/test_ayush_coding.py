import pytest
from app.models.encounter import Encounter
from app.models.symptom import Symptom
from app.services.ayush_coding_service import (
    _match_term,
    build_dashavidha_pariksha_context,
    map_ayush_codes,
)


def test_ayush_catalog_lookup_known_terms():
    """Verify official NAMASTE and WHO ICD-11 Chapter 26 dual codes map deterministically."""
    # Fever / Jvara
    fever_match = _match_term("Patient has high fever and chills")
    assert fever_match is not None
    assert fever_match["namaste_code"] == "NAMC-AYU-001"
    assert "Jvara" in fever_match["namaste_term"]
    assert fever_match["who_icd11_code"] == "TM2-AYU-001"

    # Cough / Kasa
    cough_match = _match_term("persistent dry cough")
    assert cough_match is not None
    assert cough_match["namaste_code"] == "NAMC-AYU-024"
    assert "Kasa" in cough_match["namaste_term"]
    assert cough_match["who_icd11_code"] == "TM2-AYU-024"

    # Joint pain / Sandhivata
    joint_match = _match_term("severe joint pain in knees")
    assert joint_match is not None
    assert joint_match["namaste_code"] == "NAMC-AYU-042"
    assert "Sandhivata" in fever_match or "Sandhivata" in joint_match["namaste_term"]

    # Low back pain / Katishula
    back_match = _match_term("chronic low back pain with stiffness")
    assert back_match is not None
    assert back_match["namaste_code"] == "NAMC-AYU-088"

    # Diabetes / Madhumeha
    diabetes_match = _match_term("history of diabetes mellitus")
    assert diabetes_match is not None
    assert diabetes_match["namaste_code"] == "NAMC-AYU-055"
    assert "Madhumeha" in diabetes_match["namaste_term"]


def test_ayush_catalog_zero_hallucination_on_unknown_terms():
    """Verify that uncatalogued complaints are marked unmapped without hallucinating codes."""
    unknown_match = _match_term("fractured left clavicle while skateboarding")
    assert unknown_match is None


def test_ayush_coding_endpoint(client, synthetic_patient):
    test_client, session_maker = client
    patient_id = synthetic_patient["id"]

    # Add an encounter and symptom
    with session_maker() as db:
        encounter = Encounter(
            patient_id=patient_id,
            language="en",
            chief_complaint="fever for three days and dry cough",
        )
        db.add(encounter)
        db.commit()
        db.refresh(encounter)

        symptom = Symptom(
            encounter_id=encounter.id,
            name="fever",
            description="high fever",
        )
        db.add(symptom)
        db.commit()

    # Call endpoint
    resp = test_client.get(f"/patients/{patient_id}/ayush-coding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == patient_id
    assert data["coding_status"] == "mapped"
    assert len(data["codes"]) >= 1

    # Find the fever code entry
    fever_entry = next((c for c in data["codes"] if c["namaste_code"] == "NAMC-AYU-001"), None)
    assert fever_entry is not None
    assert fever_entry["who_icd11_code"] == "TM2-AYU-001"
    assert fever_entry["system"] == "Ayurveda"
    assert fever_entry["coding_status"] == "mapped"
    assert fever_entry["is_physician_verified"] is False

    # Check Dashavidha Pariksha
    dashavidha = data["dashavidha_pariksha_context"]
    assert dashavidha is not None
    assert len(dashavidha) == 10
    assert "1_prakriti" in dashavidha
    assert "10_vaya" in dashavidha
