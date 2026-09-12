from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine, ensure_consent_columns, ensure_document_upload_columns
from app.models import Patient
from app.models import Allergy, Consultation, Consent, Document, Encounter, Medication, OCRResult, Symptom
from app.api.patients import router as patient_router
from app.api.intake import router as intake_router
from app.api.documents import router as documents_router
from app.api.clinical_summary import router as clinical_summary_router
from app.api.consent import router as consent_router


ensure_document_upload_columns()
ensure_consent_columns()
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MediKiosk API",
    description="AI-powered Clinical History Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(patient_router)
app.include_router(intake_router)
app.include_router(documents_router)
app.include_router(clinical_summary_router)
app.include_router(consent_router)


@app.get("/")
def root():
    return {
        "message": "MediKiosk Backend is running 🚀"
    }