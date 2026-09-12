import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.encounter import Encounter
from app.models.patient import Patient
from app.models.symptom import Symptom
from app.schemas.intake import (
    ClinicalOutput,
    IntakeMessageRequest,
    IntakeMessageResponse,
    IntakeStartRequest,
    IntakeStartResponse,
    RedFlag,
)
from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
    generate_clinical_response,
)


router = APIRouter(prefix="/intake", tags=["Clinical Intake"])

INITIAL_QUESTION = (
    "Hello. I will help collect your medical history before you meet the doctor. "
    "What is the main problem or symptom you are experiencing today?"
)

# The API owns active context; durable clinical facts are stored in ORM rows.
_conversations: dict[int, list[dict[str, str]]] = {}


def _red_flags_for_message(message: str) -> list[RedFlag]:
    patterns = (
        r"severe chest pain|chest pain.*(severe|crushing|pressure)",
        r"(severe|very bad|cannot) .*breath|difficulty breathing|shortness of breath",
        r"loss of consciousness|passed out|unconscious",
        r"uncontrolled bleeding|bleeding heavily|bleeding a lot",
        r"sudden.*(weakness|numbness|paralysis|confusion|speech)",
    )
    if any(re.search(pattern, message.lower()) for pattern in patterns):
        return [
            RedFlag(
                type="urgent_symptom",
                severity="high",
                message="Potential urgent symptom reported; staff review required.",
            )
        ]
    return []


def _parse_ai_output(raw: str) -> ClinicalOutput:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()
    try:
        return ClinicalOutput.model_validate(json.loads(candidate))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned malformed clinical data.",
        ) from exc


def _persist_clinical_data(
    db: Session, encounter: Encounter, clinical_data: dict[str, Any]
) -> None:
    def text_value(value: Any) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    chief_complaint = clinical_data.get("chief_complaint")
    chief_complaint_text = text_value(chief_complaint)
    if chief_complaint_text:
        encounter.chief_complaint = chief_complaint_text

    if not chief_complaint_text:
        return

    db.add(
        Symptom(
            encounter_id=encounter.id,
            name=chief_complaint_text,
            duration=text_value(clinical_data.get("duration")),
            severity=text_value(clinical_data.get("severity")),
            location=text_value(clinical_data.get("location")),
            description=text_value(clinical_data.get("character")),
        )
    )


@router.post("/start", response_model=IntakeStartResponse, status_code=201)
def start_intake(
    request: IntakeStartRequest, db: Session = Depends(get_db)
) -> IntakeStartResponse:
    patient = db.get(Patient, request.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    encounter = Encounter(
        patient_id=patient.id,
        language=request.language,
        status="collecting",
    )
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    _conversations[encounter.id] = []

    return IntakeStartResponse(
        encounter_id=encounter.id,
        assistant_message=INITIAL_QUESTION,
        status="collecting",
    )


@router.post("/message", response_model=IntakeMessageResponse)
async def send_intake_message(
    request: IntakeMessageRequest, db: Session = Depends(get_db)
) -> IntakeMessageResponse:
    encounter = db.get(Encounter, request.encounter_id)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    if encounter.status != "collecting":
        raise HTTPException(status_code=409, detail="Encounter is not active")
    if db.get(Patient, encounter.patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    conversation = _conversations.setdefault(encounter.id, [])
    conversation.append({"role": "user", "content": request.message})
    local_flags = _red_flags_for_message(request.message)

    try:
        raw_response = await generate_clinical_response(
            conversation, language=encounter.language
        )
    except AIAuthenticationError as exc:
        raise HTTPException(status_code=502, detail="AI provider authentication failed.") from exc
    except AIRateLimitError as exc:
        raise HTTPException(
            status_code=503,
            detail="AI provider is temporarily unavailable. Please try again later.",
        ) from exc
    except AITimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except AIConnectionError as exc:
        raise HTTPException(status_code=503, detail="AI provider could not be reached.") from exc
    except AIUpstreamError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid response.") from exc

    output = _parse_ai_output(raw_response)
    all_flags = local_flags + output.red_flags
    if local_flags and output.status == "collecting":
        output.status = "needs_staff_attention"
    _persist_clinical_data(db, encounter, output.clinical_data)
    encounter.status = output.status
    if output.status != "collecting":
        encounter.completed_at = datetime.now(timezone.utc)
    db.commit()

    conversation.append({"role": "assistant", "content": output.assistant_message})
    return IntakeMessageResponse(
        encounter_id=encounter.id,
        assistant_message=output.assistant_message,
        status=output.status,
        extracted_data=output.clinical_data,
        red_flags=all_flags,
    )


@router.post(
    "/{encounter_id}/terminate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Terminate an active intake session"
)
def terminate_intake_session(
    encounter_id: int,
    db: Session = Depends(get_db)
):
    """Terminate an active intake session and clear conversation state."""
    encounter = db.get(Encounter, encounter_id)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Encounter not found")
    
    if encounter.status != "collecting":
        raise HTTPException(status_code=409, detail="Encounter is not active")
    
    # Clear conversation state
    _conversations.pop(encounter_id, None)
    
    # Mark encounter as terminated
    encounter.status = "terminated"
    encounter.completed_at = datetime.now(timezone.utc)
    db.commit()
    
    return None