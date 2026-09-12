import asyncio
import json
import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import Document
from app.models.encounter import Encounter
from app.models.ocr_result import OCRResult
from app.models.patient import Patient
from app.schemas.document import DocumentResponse
from app.schemas.document import OCRResponse
from app.schemas.document import DocumentExtractionResponse
from app.services.ai_service import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    AITimeoutError,
    AIUpstreamError,
)
from app.services.ocr_service import extract_document_text
from app.services.medical_extraction_service import generate_medical_extraction
from app.schemas.medical_extraction import MedicalExtraction
from app.schemas.document_intelligence import DocumentIntelligenceResponse
from app.services.document_intelligence_service import build_document_intelligence


router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 10 * 1024 * 1024
STORAGE_DIRECTORY = Path(__file__).resolve().parents[2] / "storage" / "documents"

ALLOWED_TYPES = {
    "application/pdf": (b"%PDF", ".pdf"),
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
}


def _safe_original_name(filename: str | None) -> str:
    name = Path(filename or "document").name
    return name[:255] or "document"


async def _store_upload(file: UploadFile, destination: Path, signature: bytes) -> int:
    total = 0
    first_chunk = True
    try:
        with destination.open("xb") as output:
            while chunk := await file.read(1024 * 1024):
                if first_chunk and not chunk.startswith(signature):
                    raise HTTPException(status_code=415, detail="File content does not match its MIME type.")
                first_chunk = False
                total += len(chunk)
                if total > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File exceeds the 10 MB size limit.")
                output.write(chunk)
            if first_chunk:
                raise HTTPException(status_code=415, detail="Uploaded file is empty.")
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except OSError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not store document.") from exc
    finally:
        await file.close()
    return total


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a validated medical document",
)
async def upload_document(
    patient_id: int = Form(...),
    encounter_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    encounter = None
    if encounter_id is not None:
        encounter = db.get(Encounter, encounter_id)
        if encounter is None:
            raise HTTPException(status_code=404, detail="Encounter not found")
        if encounter.patient_id != patient_id:
            raise HTTPException(status_code=400, detail="Encounter does not belong to patient")

    file_type = ALLOWED_TYPES.get(file.content_type or "")
    if file_type is None:
        await file.close()
        raise HTTPException(status_code=415, detail="Unsupported document type")

    STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{file_type[1]}"
    destination = STORAGE_DIRECTORY / stored_name
    file_size = await _store_upload(file, destination, file_type[0])

    document = Document(
        patient_id=patient_id,
        encounter_id=encounter_id,
        file_name=_safe_original_name(file.filename),
        file_url=f"documents/{stored_name}",
        document_type=file.content_type,
        content_type=file.content_type,
        file_size=file_size,
        ocr_status="uploaded",
    )
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception as exc:
        db.rollback()
        await asyncio.to_thread(destination.unlink, True)
        raise HTTPException(status_code=500, detail="Could not save document metadata.") from exc
    return document


@router.post(
    "/{document_id}/ocr",
    response_model=OCRResponse,
    summary="Extract text from a stored document",
)
async def process_document_ocr(
    document_id: int, db: Session = Depends(get_db)
) -> OCRResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    path = (STORAGE_DIRECTORY / Path(document.file_url).name).resolve()
    if path.parent != STORAGE_DIRECTORY.resolve() or not path.is_file():
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=404, detail="Stored document file not found")

    document.ocr_status = "processing"
    db.commit()
    try:
        result = await extract_document_text(path, document.content_type)
    except FileNotFoundError as exc:
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=404, detail="Stored document file not found") from exc
    except AIAuthenticationError as exc:
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="OCR provider authentication failed.") from exc
    except AIRateLimitError as exc:
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=503, detail="OCR provider is temporarily unavailable.") from exc
    except AITimeoutError as exc:
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=504, detail="OCR provider request timed out.") from exc
    except AIConnectionError as exc:
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=503, detail="OCR provider could not be reached.") from exc
    except AIUpstreamError as exc:
        document.ocr_status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail="OCR provider returned invalid data.") from exc

    ocr_result = OCRResult(
        document_id=document.id,
        extracted_text=result["text"],
        structured_data=result,
    )
    db.add(ocr_result)
    document.ocr_status = "completed"
    db.commit()
    return OCRResponse(
        document_id=document.id,
        status=document.ocr_status,
        extracted_text=result["text"],
        structured_data=result,
    )


def _parse_medical_extraction(raw: str) -> MedicalExtraction:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()
    try:
        parsed = json.loads(candidate)
        required = {
            "patient", "document", "observations", "medications", "allergies",
            "diagnoses_or_conditions", "procedures", "clinical_notes",
        }
        if not isinstance(parsed, dict) or set(required) - set(parsed):
            raise ValueError("required extraction fields are missing")
        return MedicalExtraction.model_validate(parsed)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="AI returned invalid medical extraction data.") from exc


@router.post(
    "/{document_id}/extract",
    response_model=DocumentExtractionResponse,
    summary="Extract explicitly stated medical information from OCR text",
)
async def extract_document_information(
    document_id: int, db: Session = Depends(get_db)
) -> DocumentExtractionResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    ocr_result = (
        db.query(OCRResult)
        .filter(OCRResult.document_id == document_id)
        .order_by(OCRResult.id.desc())
        .first()
    )
    if ocr_result is None:
        raise HTTPException(status_code=404, detail="OCR result not found")
    if not ocr_result.extracted_text or not ocr_result.extracted_text.strip():
        raise HTTPException(status_code=422, detail="OCR result does not contain text")

    try:
        raw = await generate_medical_extraction(ocr_result.extracted_text)
    except AIAuthenticationError as exc:
        raise HTTPException(status_code=503, detail="AI provider authentication failed.") from exc
    except AIRateLimitError as exc:
        raise HTTPException(status_code=503, detail="AI provider is temporarily unavailable.") from exc
    except AITimeoutError as exc:
        raise HTTPException(status_code=504, detail="AI provider request timed out.") from exc
    except AIConnectionError as exc:
        raise HTTPException(status_code=502, detail="AI provider could not be reached.") from exc
    except AIUpstreamError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned an invalid response.") from exc

    extraction = _parse_medical_extraction(raw)
    stored_data = dict(ocr_result.structured_data or {})
    stored_data["medical_extraction"] = extraction.model_dump(mode="json")
    ocr_result.structured_data = stored_data
    db.commit()
    return DocumentExtractionResponse(
        document_id=document.id,
        ocr_result_id=ocr_result.id,
        extraction=extraction,
    )


@router.get(
    "/{document_id}/intelligence",
    response_model=DocumentIntelligenceResponse,
    summary="Organize extracted document information for physician review",
)
def get_document_intelligence(
    document_id: int, db: Session = Depends(get_db)
) -> DocumentIntelligenceResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    ocr_result = (
        db.query(OCRResult)
        .filter(OCRResult.document_id == document_id)
        .order_by(OCRResult.id.desc())
        .first()
    )
    if ocr_result is None:
        raise HTTPException(status_code=404, detail="OCR result not found")
    structured_data = ocr_result.structured_data or {}
    medical_extraction = structured_data.get("medical_extraction")
    if not isinstance(medical_extraction, dict):
        raise HTTPException(status_code=404, detail="Medical extraction not found")
    try:
        return build_document_intelligence(
            document_id=document.id,
            ocr_result_id=ocr_result.id,
            extraction=medical_extraction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Stored medical extraction is invalid.") from exc