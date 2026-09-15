from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.database import (
    Base, engine, ensure_consent_columns, ensure_document_upload_columns,
    ensure_patient_abha_index, ensure_physician_review_columns,
    ensure_queue_priority_columns
)
from app.models import Patient
from app.models import Allergy, Consultation, Consent, Document, Encounter, Medication, OCRResult, PhysicianReviewAudit, Symptom
from app.api.patients import router as patient_router
from app.api.intake import router as intake_router
from app.api.documents import router as documents_router
from app.api.clinical_summary import router as clinical_summary_router
from app.api.consent import router as consent_router
from app.api.abdm import router as abdm_router
from app.api.physician_review import router as physician_review_router


try:
    ensure_document_upload_columns()
    ensure_consent_columns()
    ensure_physician_review_columns()
    ensure_queue_priority_columns()
    Base.metadata.create_all(bind=engine)
    ensure_patient_abha_index()
except Exception as exc:
    import logging
    logging.getLogger("uvicorn.error").warning(f"Database schema auto-init deferred: {exc}")


app = FastAPI(
    title="MediKiosk API",
    description="AI-powered Clinical History Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://medikiosk-ebon.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(patient_router)
app.include_router(intake_router)
app.include_router(documents_router)
app.include_router(clinical_summary_router)
app.include_router(consent_router)
app.include_router(abdm_router)
app.include_router(physician_review_router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/kiosk", StaticFiles(directory=frontend_dir, html=True), name="kiosk")


@app.get("/healthz")
def healthz():
    return {
        "status": "ok"
    }


@app.get("/")
def root():
    return {
        "message": "MediKiosk Backend is running 🚀"
    }

