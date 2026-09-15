"""FHIR R4 representation service for MediKiosk clinical cases.

Aligns with NRCES India FHIR R4 Implementation Guide profiles
(Patient, Encounter, Condition, Observation, MedicationStatement, AllergyIntolerance).
"""
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.models.allergy import Allergy
from app.models.document import Document
from app.models.encounter import Encounter
from app.models.medication import Medication
from app.models.ocr_result import OCRResult
from app.models.patient import Patient
from app.models.symptom import Symptom


def generate_fhir_r4_bundle(
    db: Session, patient_id: int, encounter_id: int | None = None
) -> dict[str, Any]:
    patient = db.get(Patient, patient_id)
    if not patient:
        return {}

    encounter = None
    if encounter_id:
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id, Encounter.patient_id == patient_id).first()
    else:
        encounter = db.query(Encounter).filter(Encounter.patient_id == patient_id).order_by(Encounter.started_at.desc()).first()

    bundle_id = f"medikiosk-bundle-{patient_id}-{encounter.id if encounter else '0'}"
    timestamp = datetime.now(timezone.utc).isoformat()

    entries: list[dict[str, Any]] = []

    # 1. Patient Resource
    identifiers = [
        {
            "system": "https://hospital.local/patient-id",
            "value": str(patient.id),
            "type": {"text": "Hospital Patient ID"},
        }
    ]
    if patient.abha_id:
        identifiers.append({
            "system": "https://healthid.ndhm.gov.in",
            "value": patient.abha_id,
            "type": {"text": "ABHA Number"},
        })

    patient_resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "identifier": identifiers,
        "active": True,
        "name": [{"use": "official", "text": patient.name}],
        "gender": "female" if patient.gender == "female" else ("male" if patient.gender == "male" else "other"),
    }
    if patient.phone:
        patient_resource["telecom"] = [{"system": "phone", "value": patient.phone}]

    entries.append({
        "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'patient-{patient.id}')}",
        "resource": patient_resource,
    })

    # 2. Encounter Resource
    if encounter:
        enc_priority = getattr(encounter, "priority", "routine") or "routine"
        encounter_resource: dict[str, Any] = {
            "resourceType": "Encounter",
            "id": str(encounter.id),
            "status": "in-progress" if encounter.status == "collecting" else "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": {
                "reference": f"Patient/{patient.id}",
                "display": patient.name,
            },
            "priority": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                        "code": "EM" if enc_priority == "urgent" else ("UR" if enc_priority == "priority" else "R"),
                        "display": enc_priority.capitalize(),
                    }
                ],
                "text": enc_priority,
            },
            "period": {
                "start": encounter.started_at.isoformat() if encounter.started_at else timestamp,
            },
        }
        if encounter.chief_complaint:
            encounter_resource["reasonCode"] = [{"text": encounter.chief_complaint}]

        entries.append({
            "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'encounter-{encounter.id}')}",
            "resource": encounter_resource,
        })

        # 3. Condition Resources (Symptoms & Chief Complaint)
        symptoms = db.query(Symptom).filter(Symptom.encounter_id == encounter.id).all()
        for idx, s in enumerate(symptoms):
            condition_resource: dict[str, Any] = {
                "resourceType": "Condition",
                "id": f"symptom-{s.id}",
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active",
                        }
                    ]
                },
                "verificationStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": "unconfirmed",
                        }
                    ],
                    "text": "Patient Reported / Unverified",
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                "code": "problem-list-item",
                            }
                        ]
                    }
                ],
                "code": {"text": s.name},
                "subject": {"reference": f"Patient/{patient.id}", "display": patient.name},
                "encounter": {"reference": f"Encounter/{encounter.id}"},
            }
            if s.severity:
                condition_resource["severity"] = {"text": s.severity}
            if s.description or s.duration:
                notes = []
                if s.duration:
                    notes.append(f"Duration: {s.duration}")
                if s.description:
                    notes.append(s.description)
                condition_resource["note"] = [{"text": "; ".join(notes)}]

            entries.append({
                "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'condition-symptom-{s.id}')}",
                "resource": condition_resource,
            })

    # 4. Observation Resources from OCR Results
    ocr_results = (
        db.query(OCRResult)
        .join(Document, OCRResult.document_id == Document.id)
        .filter(Document.patient_id == patient.id)
        .all()
    )
    obs_count = 0
    for r in ocr_results:
        if isinstance(r.structured_data, dict):
            ext = r.structured_data.get("medical_extraction", {})
            if isinstance(ext, dict):
                observations = ext.get("observations", [])
                for obs in observations:
                    obs_count += 1
                    obs_name = obs.get("name") if isinstance(obs, dict) else str(obs)
                    obs_val = obs.get("value") if isinstance(obs, dict) else None
                    obs_unit = obs.get("unit") if isinstance(obs, dict) else None
                    obs_range = obs.get("reference_range") if isinstance(obs, dict) else None
                    obs_status = obs.get("status") if isinstance(obs, dict) else None

                    obs_resource: dict[str, Any] = {
                        "resourceType": "Observation",
                        "id": f"obs-{r.id}-{obs_count}",
                        "status": "registered",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "laboratory",
                                    }
                                ]
                            }
                        ],
                        "code": {"text": obs_name},
                        "subject": {"reference": f"Patient/{patient.id}", "display": patient.name},
                    }
                    if encounter:
                        obs_resource["encounter"] = {"reference": f"Encounter/{encounter.id}"}
                    if obs_val is not None:
                        obs_resource["valueString"] = str(obs_val)
                    if obs_range:
                        obs_resource["referenceRange"] = [{"text": str(obs_range)}]
                    if obs_status:
                        obs_resource["interpretation"] = [{"text": str(obs_status)}]

                    entries.append({
                        "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'observation-{r.id}-{obs_count}')}",
                        "resource": obs_resource,
                    })

                # Conditions/Diagnoses from OCR
                conditions = ext.get("diagnoses_or_conditions", [])
                for idx, c in enumerate(conditions):
                    c_text = c.get("text") if isinstance(c, dict) else str(c)
                    if c_text:
                        entries.append({
                            "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'condition-ocr-{r.id}-{idx}')}",
                            "resource": {
                                "resourceType": "Condition",
                                "id": f"ocr-cond-{r.id}-{idx}",
                                "clinicalStatus": {
                                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                                },
                                "code": {"text": c_text},
                                "subject": {"reference": f"Patient/{patient.id}", "display": patient.name},
                                "note": [{"text": "Extracted from source document OCR text; unverified by physician."}],
                            },
                        })

    # 5. MedicationStatement Resources
    patient_meds = db.query(Medication).filter(Medication.patient_id == patient.id).all()
    for m in patient_meds:
        med_resource: dict[str, Any] = {
            "resourceType": "MedicationStatement",
            "id": f"med-{m.id}",
            "status": "active",
            "medicationCodeableConcept": {"text": m.name},
            "subject": {"reference": f"Patient/{patient.id}", "display": patient.name},
        }
        dosage_parts = [p for p in [m.dosage, m.frequency] if p]
        if dosage_parts:
            med_resource["dosage"] = [{"text": " ".join(dosage_parts)}]

        entries.append({
            "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'medication-{m.id}')}",
            "resource": med_resource,
        })

    # 6. AllergyIntolerance Resources
    patient_allergies = db.query(Allergy).filter(Allergy.patient_id == patient.id).all()
    for a in patient_allergies:
        allergy_resource: dict[str, Any] = {
            "resourceType": "AllergyIntolerance",
            "id": f"allergy-{a.id}",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active",
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                        "code": "unconfirmed",
                    }
                ]
            },
            "code": {"text": a.allergen},
            "patient": {"reference": f"Patient/{patient.id}", "display": patient.name},
        }
        if a.reaction:
            allergy_resource["reaction"] = [{"manifestation": [{"text": a.reaction}]}]

        entries.append({
            "fullUrl": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, f'allergy-{a.id}')}",
            "resource": allergy_resource,
        })

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": timestamp,
        "meta": {
            "profile": ["https://nrces.in/ndhm/fhir/r4/StructureDefinition/DocumentBundle"],
            "tag": [
                {
                    "system": "https://medikiosk.in/tags",
                    "code": "pre-consultation-intake",
                    "display": "MediKiosk Pre-Consultation Clinical Intake",
                }
            ],
        },
        "total": len(entries),
        "entry": entries,
    }
