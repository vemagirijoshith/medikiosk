import pytest
from app.models.allergy import Allergy
from app.models.encounter import Encounter
from app.models.medication import Medication
from app.models.ocr_result import OCRResult
from app.models.symptom import Symptom
from app.services.fhir_service import generate_fhir_r4_bundle


def test_fhir_bundle_generation(client, synthetic_patient):
    test_client, session_maker = client
    patient_id = synthetic_patient["id"]

    with session_maker() as db:
        encounter = Encounter(
            patient_id=patient_id,
            language="en",
            chief_complaint="persistent cough and throat irritation",
        )
        db.add(encounter)
        db.commit()
        db.refresh(encounter)

        symptom = Symptom(
            encounter_id=encounter.id,
            name="cough",
            description="dry barking cough for 4 days",
        )
        db.add(symptom)

        med = Medication(
            patient_id=patient_id,
            name="Amoxicillin 500mg",
            dosage="500mg",
            frequency="TDS",
            source="intake",
        )
        db.add(med)

        allergy = Allergy(
            patient_id=patient_id,
            allergen="Penicillin",
            reaction="skin hives and itching",
        )
        db.add(allergy)

        db.commit()

        bundle = generate_fhir_r4_bundle(db, patient_id, encounter.id)

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert "timestamp" in bundle
    assert len(bundle["entry"]) >= 4

    resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Encounter" in resource_types
    assert "Condition" in resource_types
    assert "MedicationStatement" in resource_types
    assert "AllergyIntolerance" in resource_types

    # Validate Patient resource
    patient_res = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
    assert patient_res["id"] == str(patient_id)
    assert patient_res["name"][0]["text"] == synthetic_patient["name"]

    # Validate AllergyIntolerance resource
    allergy_res = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "AllergyIntolerance")
    assert allergy_res["code"]["text"] == "Penicillin"


def test_fhir_endpoint(client, synthetic_patient):
    test_client, session_maker = client
    patient_id = synthetic_patient["id"]

    with session_maker() as db:
        encounter = Encounter(
            patient_id=patient_id,
            language="en",
            chief_complaint="routine checkup",
        )
        db.add(encounter)
        db.commit()

    resp = test_client.get(f"/patients/{patient_id}/fhir")
    assert resp.status_code == 200
    bundle = resp.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
