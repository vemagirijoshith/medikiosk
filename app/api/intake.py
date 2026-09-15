import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.consultation import Consultation
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
    TranscriptionResponse,
)
from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
    generate_clinical_response,
)
from app.services.transcription_service import transcribe_audio


router = APIRouter(prefix="/intake", tags=["Clinical Intake"])

INITIAL_QUESTION = (
    "Hello. I will help collect your medical history before you meet the doctor. "
    "What is the main problem or symptom you are experiencing today?"
)

INITIAL_QUESTIONS = {
    "en": INITIAL_QUESTION,
    "hi": "नमस्ते। डॉक्टर से मिलने से पहले मैं आपका स्वास्थ्य इतिहास एकत्र करने में मदद करूँगा। आज आपको मुख्य समस्या या लक्षण क्या है?",
    "te": "నమస్కారం. మీరు వైద్యుడిని కలిసే ముందు మీ ఆరోగ్య చరిత్రను సేకరించడంలో నేను సహాయం చేస్తాను. ఈ రోజు మీరు ఎదుర్కొంటున్న ప్రధాన సమస్య లేదా లక్షణం ఏమిటి?",
    "ta": "வணக்கம். மருத்துவரை சந்திப்பதற்கு முன் உங்கள் மருத்துவ வரலாற்றை சேகரிக்க நான் உதவுகிறேன். இன்று நீங்கள் சந்திக்கும் முக்கிய பிரச்சனை அல்லது அறிகுறி என்ன?",
    "bn": "নমস্কার। ডাক্তারের সাথে দেখা করার আগে আমি আপনার চিকিৎসার ইতিহাস সংগ্রহ করতে সাহায্য করব। আজ আপনার প্রধান সমস্যা বা উপসর্গ কী?",
}

# The API owns active context; durable clinical facts are stored in ORM rows.
_conversations: dict[int, list[dict[str, str]]] = {}


def _red_flags_for_message(message: str) -> list[RedFlag]:
    patterns = (
        (r"chest pain|chest tightness|chest pressure|crushing chest|angina|heart attack", "Chest pain or potential cardiac distress reported"),
        (r"breathless|shortness of breath|difficulty breathing|cannot breathe|trouble breathing|struggling to breathe", "Severe respiratory distress or breathlessness reported"),
        (r"loss of consciousness|passed out|unconscious|fainted|fainting|blackout|blacked out|seizure|convulsion", "Loss of consciousness, fainting, or neurological event reported"),
        (r"uncontrolled bleeding|bleeding heavily|bleeding a lot|vomiting blood|coughing up blood|active bleeding|severe bleeding", "Severe or uncontrolled bleeding reported"),
        (r"sudden.*(weakness|numbness|paralysis|confusion|speech)|facial droop|slurred speech|stroke", "Acute neurological weakness or stroke signs reported"),
        (r"severe dizziness|sudden dizziness|extreme dizziness", "Severe acute dizziness reported"),
    )
    lower = message.lower()
    flags = []
    for pattern, reason in patterns:
        if re.search(pattern, lower):
            flags.append(
                RedFlag(
                    type="urgent_symptom",
                    severity="high",
                    message=f"Potential urgent symptom: {reason}. Immediate healthcare professional evaluation recommended.",
                )
            )
    return flags


def _parse_ai_output(raw: str) -> ClinicalOutput:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()

    if "{" in candidate and "}" in candidate:
        start = candidate.find("{")
        end = candidate.rfind("}") + 1
        candidate_json = candidate[start:end]
    else:
        candidate_json = candidate

    try:
        data = json.loads(candidate_json)
        if isinstance(data, dict):
            raw_flags = data.get("red_flags")
            if isinstance(raw_flags, list):
                norm_flags = []
                for f in raw_flags:
                    if isinstance(f, str):
                        norm_flags.append({
                            "type": "urgent_symptom",
                            "severity": "high",
                            "message": f,
                        })
                    elif isinstance(f, dict):
                        norm_flags.append(f)
                data["red_flags"] = norm_flags
            elif isinstance(raw_flags, str):
                data["red_flags"] = [{
                    "type": "urgent_symptom",
                    "severity": "high",
                    "message": raw_flags,
                }]

            if data.get("status") not in {"collecting", "ready_for_review", "needs_staff_attention"}:
                data["status"] = "collecting"

        return ClinicalOutput.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider returned malformed clinical data.",
        ) from exc


def _persist_clinical_data(
    db: Session, encounter: Encounter, clinical_data: dict[str, Any]
) -> None:
    def text_value(value: Any) -> str | None:
        if value is None:
            return None
        s = str(value).strip()
        return s if s else None

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

    initial_msg = INITIAL_QUESTIONS.get(request.language, INITIAL_QUESTION)

    return IntakeStartResponse(
        encounter_id=encounter.id,
        assistant_message=initial_msg,
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

    # Emergency queue priority: monotonic escalation (only moves up, never down)
    if all_flags or local_flags:
        encounter.priority = "urgent"
        reasons = [f.message for f in (local_flags or all_flags) if getattr(f, 'message', None)]
        encounter.red_flag_reason = "; ".join(reasons) if reasons else "Urgent clinical symptom flagged during intake"
    elif getattr(encounter, "priority", None) is None:
        encounter.priority = "routine"

    _persist_clinical_data(db, encounter, output.clinical_data)
    encounter.status = output.status
    if output.status != "collecting":
        encounter.completed_at = datetime.now(timezone.utc)

    consultation = db.query(Consultation).filter(Consultation.encounter_id == encounter.id).first()
    if consultation and encounter.priority == "urgent":
        consultation.priority = "urgent"
        consultation.red_flag_reason = encounter.red_flag_reason

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


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe spoken audio via Groq Whisper",
)
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str | None = Form(None),
) -> TranscriptionResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing audio file.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds 25 MB limit.",
        )

    try:
        transcript = await transcribe_audio(
            file_bytes=content,
            filename=file.filename or "recording.webm",
            content_type=file.content_type or "audio/webm",
            language=language,
        )
    except AIAuthenticationError as exc:
        raise HTTPException(status_code=502, detail="Transcription authentication failed.") from exc
    except AIRateLimitError as exc:
        raise HTTPException(status_code=503, detail="Transcription service is rate-limited.") from exc
    except AITimeoutError as exc:
        raise HTTPException(status_code=504, detail="Transcription request timed out.") from exc
    except AIConnectionError as exc:
        raise HTTPException(status_code=503, detail="Transcription service could not be reached.") from exc
    except AIUpstreamError as exc:
        raise HTTPException(status_code=502, detail="Transcription service returned an error.") from exc

    return TranscriptionResponse(transcript=transcript, language=language)