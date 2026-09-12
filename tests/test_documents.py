from pathlib import Path
from unittest.mock import patch

from app.api import documents as documents_api
from app.db.database import Base
from app.models import Document, Encounter, Patient


PDF = b"%PDF-1.7\nsynthetic document\n"
PNG = b"\x89PNG\r\n\x1a\nsynthetic image\n"


def upload(client, patient_id, content, filename="record.pdf", content_type="application/pdf", encounter_id=None):
    data = {"patient_id": str(patient_id)}
    if encounter_id is not None:
        data["encounter_id"] = str(encounter_id)
    return client.post(
        "/documents/upload",
        data=data,
        files={"file": (filename, content, content_type)},
    )


def test_valid_pdf_upload_persists_metadata_and_uses_uuid_storage(client, synthetic_patient, tmp_path):
    test_client, session_factory = client
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        response = upload(test_client, synthetic_patient["id"], PDF)

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["patient_id"] == synthetic_patient["id"]
    assert payload["filename"] == "record.pdf"
    assert payload["content_type"] == "application/pdf"
    assert payload["file_size"] == len(PDF)
    assert payload["status"] == "uploaded"
    stored = list(tmp_path.iterdir())
    assert len(stored) == 1
    assert stored[0].suffix == ".pdf"
    assert stored[0].name != "record.pdf"
    assert len(Path(stored[0]).stem) == 32
    db = session_factory()
    try:
        document = db.get(Document, payload["id"])
        assert document is not None
        assert document.file_url == f"documents/{stored[0].name}"
    finally:
        db.close()


def test_valid_png_upload_succeeds(client, synthetic_patient, tmp_path):
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        response = upload(
            client[0], synthetic_patient["id"], PNG, "scan.png", "image/png"
        )
    assert response.status_code == 201
    assert response.json()["content_type"] == "image/png"


def test_rejects_unsupported_type_and_bad_signature(client, synthetic_patient, tmp_path):
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        unsupported = upload(
            client[0], synthetic_patient["id"], b"plain text", "note.txt", "text/plain"
        )
        invalid = upload(
            client[0], synthetic_patient["id"], b"not a pdf", "record.pdf", "application/pdf"
        )
    assert unsupported.status_code == 415
    assert invalid.status_code == 415
    assert list(tmp_path.iterdir()) == []


def test_rejects_upload_over_10_mb(client, synthetic_patient, tmp_path):
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        response = upload(
            client[0], synthetic_patient["id"], PDF + b"x" * (10 * 1024 * 1024),
        )
    assert response.status_code == 413
    assert list(tmp_path.iterdir()) == []


def test_validates_patient_and_encounter_relationship(client, synthetic_patient, tmp_path):
    test_client, session_factory = client
    db = session_factory()
    other_patient = Patient(name="Other Synthetic Patient", age=41, gender="unknown", language="en")
    db.add(other_patient)
    db.commit()
    db.refresh(other_patient)
    encounter = Encounter(patient_id=other_patient.id, language="en", status="collecting")
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    other_patient_id = other_patient.id
    encounter_id = encounter.id
    db.close()
    try:
        with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
            missing = upload(test_client, 999999, PDF)
            bad_encounter = upload(test_client, synthetic_patient["id"], PDF, encounter_id=999999)
            wrong_owner = upload(test_client, synthetic_patient["id"], PDF, encounter_id=encounter_id)
        assert missing.status_code == 404
        assert bad_encounter.status_code == 404
        assert wrong_owner.status_code == 400
    finally:
        db = session_factory()
        db.query(Encounter).filter(Encounter.id == encounter_id).delete()
        db.query(Patient).filter(Patient.id == other_patient_id).delete()
        db.commit()
        db.close()


def test_storage_is_removed_when_database_insert_fails(client, synthetic_patient, tmp_path):
    test_client, _ = client
    with patch.object(documents_api, "STORAGE_DIRECTORY", tmp_path):
        with patch("app.api.documents.Session.commit", side_effect=RuntimeError("synthetic failure")):
            response = upload(test_client, synthetic_patient["id"], PDF)
    assert response.status_code == 500
    assert list(tmp_path.iterdir()) == []