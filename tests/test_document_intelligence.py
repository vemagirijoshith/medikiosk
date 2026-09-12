from app.models import Document, OCRResult
from app.services.document_intelligence_service import (
    build_document_intelligence,
    build_timeline,
)


def extraction(date="2026-08-12", observations=None):
    return {
        "patient": {"name": None, "age": None, "sex": None, "patient_id": None},
        "document": {"document_date": date, "document_type": "lab_report", "hospital": None, "doctor": None},
        "observations": observations or [],
        "medications": [],
        "allergies": [],
        "diagnoses_or_conditions": [],
        "procedures": [],
        "clinical_notes": [],
    }


def observation(name, value, reference_range=None, unit="g/dL"):
    return {
        "name": name,
        "value": value,
        "unit": unit,
        "reference_range": reference_range,
        "status": None,
        "source_text": f"{name}: {value} {unit}" if unit else f"{name}: {value}",
    }


def test_reference_range_statuses_and_source_traceability():
    result = build_document_intelligence(
        7,
        9,
        extraction(observations=[
            observation("Hemoglobin", "10.2", "13.0-17.0"),
            observation("Platelets", "250", "150-400", "10^9/L"),
            observation("Glucose", "220", "70-140", "mg/dL"),
            observation("Blood Pressure", "150/95", "120-130", "mmHg"),
            observation("Unknown Test", "10"),
        ]),
    )
    statuses = {item.name: item.status for item in result.highlighted_observations}
    assert statuses == {
        "Hemoglobin": "low",
        "Platelets": "normal",
        "Glucose": "high",
        "Blood Pressure": "unknown",
        "Unknown Test": "unknown",
    }
    assert result.highlighted_observations[0].document_id == 7
    assert result.highlighted_observations[0].source_text == "Hemoglobin: 10.2 g/dL"


def test_timeline_sorts_dates_and_keeps_undated_last():
    entries = build_timeline([
        (2, 20, extraction("2026-09-01")),
        (1, 10, extraction(None)),
        (3, 30, extraction("2026-08-12")),
    ])
    assert [entry.document_id for entry in entries] == [3, 2, 1]
    assert entries[-1].date is None


def test_timeline_preserves_medication_and_document_traceability():
    data = extraction()
    data["medications"] = [{
        "name": "Metformin", "dose": "500 mg", "frequency": "twice daily",
        "route": None, "duration": None, "source_text": "Metformin 500 mg twice daily",
    }]
    result = build_document_intelligence(4, 5, data)
    assert result.timeline[0].events[0].category == "medication"
    assert result.timeline[0].events[0].source_text == "Metformin 500 mg twice daily"


def test_invalid_observation_data_is_rejected():
    data = extraction(observations=[{"name": 123, "value": "10"}])
    try:
        build_document_intelligence(1, 1, data)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid observation data was accepted")


def add_document_with_extraction(test_client, session_factory, patient_id, data):
    uploaded = test_client.post(
        "/documents/upload",
        data={"patient_id": str(patient_id)},
        files={"file": ("record.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    document_id = uploaded.json()["id"]
    db = session_factory()
    db.add(OCRResult(document_id=document_id, extracted_text="synthetic", structured_data={"medical_extraction": data}))
    db.commit()
    db.close()
    return document_id


def test_intelligence_endpoint_success_and_not_found_cases(client, synthetic_patient):
    test_client, session_factory = client
    document_id = add_document_with_extraction(test_client, session_factory, synthetic_patient["id"], extraction(observations=[observation("Hemoglobin", "10.2", "13-17")]))
    response = test_client.get(f"/documents/{document_id}/intelligence")
    assert response.status_code == 200
    assert response.json()["highlighted_observations"][0]["status"] == "low"
    assert test_client.get("/documents/999999/intelligence").status_code == 404


def test_intelligence_endpoint_requires_ocr_and_b5_extraction(client, synthetic_patient):
    test_client, session_factory = client
    uploaded = test_client.post(
        "/documents/upload", data={"patient_id": str(synthetic_patient["id"])},
        files={"file": ("record.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    document_id = uploaded.json()["id"]
    assert test_client.get(f"/documents/{document_id}/intelligence").status_code == 404
    db = session_factory()
    db.add(OCRResult(document_id=document_id, extracted_text="synthetic", structured_data={"pages": []}))
    db.commit()
    db.close()
    assert test_client.get(f"/documents/{document_id}/intelligence").status_code == 404