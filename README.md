# MediKiosk — Smart Patient Caretaking & Clinical Intake Platform

> **Smart India Hackathon 2026 Prototype**  
> An AI-assisted, self-service clinical intake platform designed for fast, accurate, and dignified patient care in hospital outpatient departments (OPD).

---

## 📋 Overview

MediKiosk streamlines the hospital outpatient journey by allowing patients to self-register, provide informed consent, speak or type their symptoms in regional Indian languages, and upload physical medical reports for automated OCR extraction. Attending physicians access an unvarnished review workspace with source-backed findings, interactive field verification, and sign-off locking.

### Key Capabilities

1. **Multilingual Patient Interface (i18n)**: Real-time UI and conversational localization across **English (`en`)**, **Hindi (`hi`)**, **Telugu (`te`)**, **Tamil (`ta`)**, and **Bengali (`bn`)**.
2. **End-to-End Voice Intake**: In-browser audio recording (MediaRecorder) $\rightarrow$ FastAPI backend $\rightarrow$ **Groq Whisper (`whisper-large-v3-turbo`)** ($0.36\text{s}$) $\rightarrow$ Patient review/edit card $\rightarrow$ **Groq Clinical AI (`openai/gpt-oss-120b`)** ($1.7\text{s}$) $\rightarrow$ Dynamic clinical follow-up questions.
3. **Medical Document OCR & Intelligence**: Upload lab reports, discharge summaries, or prescriptions (PDF, PNG, JPG). Digitize via **NVIDIA Nemotron OCR v2** and extract structured observations, reference ranges, medications, and allergies with explicit source-text tracking.
4. **Granular Informed Consent Engine**: Independent grant and revocation controls across 6 purposes (`clinical_history`, `document_processing`, `document_extraction`, `clinical_summary`, `physician_review`, `abdm_sharing`).
5. **Physician Review Workspace**: Outpatient review queue, clinical packets, notes entry, affirmative verification checkboxes, and consultation sign-off with tamper-resistant audit locking.
6. **Local ABDM / ABHA Sandbox Gate**: 14-digit ABHA linking, sandbox export bundle generator, and strict consent enforcement (`403 Forbidden` on revocation).

---

## 🏗️ Architecture & Technology Stack

```
   ┌────────────────────────────────────────────────────────┐
   │             Responsive Kiosk & Physician UI            │
   │           Vanilla HTML5 / Modern CSS3 / ES6 JS         │
   └───────────────────────────┬────────────────────────────┘
                               │ HTTP / REST & Multipart Audio
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │             FastAPI Backend (Port 8001)                │
   │  • Intake & Audio Transcription (/intake/transcribe)    │
   │  • Clinical History Engine (/intake/start, /message)   │
   │  • Document & OCR Pipeline (/documents)                │
   │  • Informed Consent Service (/patients/.../consents)   │
   │  • Physician Review Audit (/patients/physician/...)    │
   │  • Local ABDM Sandbox Gate (/patients/.../abdm)        │
   └─────────────┬───────────────────────────┬──────────────┘
                 │                           │
                 ▼                           ▼
 ┌───────────────────────────────┐ ┌───────────────────────────────┐
 │       Cloud AI Services       │ │    PostgreSQL Database        │
 │ • Groq Whisper v3 Turbo       │ │ • Patients, Encounters        │
 │ • Groq GPT OSS 120B (Clinical)│ │ • Symptoms, Medications       │
 │ • NVIDIA Nemotron OCR v2      │ │ • OCR Results, Consents       │
 └───────────────────────────────┘ │ • Consultations & Audits      │
                                   └───────────────────────────────┘
```

- **Backend**: FastAPI, Pydantic v2, SQLAlchemy ORM, Uvicorn, Python-Multipart, Pillow, PyMuPDF.
- **Frontend**: Vanilla ES6+ JavaScript, modern responsive CSS design system (CSS variables, clean typography, accessible color contrast).
- **Database**: PostgreSQL (`localhost:5432/medikiosk`).
- **Clinical AI Engine**: Groq Cloud running `openai/gpt-oss-120b` (low-latency clinical reasoning and extraction).
- **Speech Engine**: Groq Cloud running `whisper-large-v3-turbo` (sub-second multilingual speech-to-text).
- **Vision Engine**: NVIDIA Cloud Functions running `nvidia/nemotron-ocr-v2` (medical document OCR).

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL server running on `localhost:5432` with database `medikiosk`
- Modern web browser (Chrome, Edge, Firefox) with microphone permissions enabled

### 1. Environment Configuration

Create or configure `.env` in the project root:

```dotenv
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/medikiosk

# Groq Cloud Clinical AI & Whisper Speech-to-Text
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-120b
GROQ_WHISPER_MODEL=whisper-large-v3-turbo

# NVIDIA Nemotron OCR v2
NVIDIA_OCR_API_KEY=nvapi-your_nvidia_ocr_key_here
NVIDIA_OCR_BASE_URL=https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2
NVIDIA_OCR_MODEL=nvidia/nemotron-ocr-v2

# ABDM Sandbox Settings
ABDM_SANDBOX_MODE=true
```

### 2. Install Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Application

```powershell
# Start FastAPI with Uvicorn
uvicorn app.main:app --reload --port 8001
```

Once running, navigate to:
- **Patient Kiosk Interface**: [http://127.0.0.1:8001/kiosk/](http://127.0.0.1:8001/kiosk/)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

---

## 🔄 User Journeys

### 1. Patient Self-Service Kiosk Flow

```
Step 1: Welcome & Start ────────► Touch Check-In or "Start with Voice"
          │
Step 2: Choose Language ────────► English, Hindi, Telugu, Tamil, Bengali
          │                       (Translates entire UI and greetings dynamically)
Step 3: Identity & Reg  ────────► Lookup by Patient ID or Register as New Patient
          │
Step 4: Informed Consent────────► Explicit grant/revoke per purpose (clinical history,
          │                       document processing, physician review, ABDM sharing)
Step 5: Guided History  ────────► Speak into microphone or type responses.
          │                       Patient confirms transcript before AI processing.
          │                       Red flag alerts for urgent symptoms.
Step 6: Documents & OCR ────────► Upload prescriptions / reports (PDF, PNG, JPG).
          │                       Instant Nemotron OCR v2 digitization & lab extraction.
Step 7: Review & Submit ────────► Review summary & submit consultation record to OPD queue.
```

### 2. Physician Clinical Workspace Flow

```
OPD Queue ──────────────────────► Inspect incoming consultation records (Pending / In Review)
    │
Review Packet ──────────────────► Review patient demographics, reported symptoms,
    │                             uploaded source reports, raw OCR text, and lab tables.
    │
Clinical Actions:
 1. Add Notes   ────────────────► Enter clinical notes -> Updates status to "in_review".
 2. Verify Data ────────────────► Select verified fields (symptoms, meds, allergies) ->
    │                             Affirmative verification updates status to "verified".
 3. Sign-off    ────────────────► Final completion locks consultation against tampering.
```

---

## 📡 API Reference

### Patient & Consent Management

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/patients/` | Register a new patient (Name, Age, Gender, Phone, ABHA) |
| `GET` | `/patients/{patient_id}` | Retrieve patient demographic record |
| `POST` | `/patients/{patient_id}/consents` | Grant purpose-specific consent (`grant` action) |
| `GET` | `/patients/{patient_id}/consents` | Retrieve full consent history and status |
| `GET` | `/patients/{patient_id}/consents/check` | Validate active consent for a specific purpose |
| `POST` | `/patients/{patient_id}/consents/{id}/revoke` | Revoke an active consent purpose |

### Clinical History & Voice Intake

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/intake/start` | Start clinical intake; returns native language initial greeting |
| `POST` | `/intake/transcribe` | Transcribe browser audio using Groq Whisper v3 Turbo |
| `POST` | `/intake/message` | Submit confirmed patient response; calls Groq GPT OSS 120B |
| `POST` | `/intake/{encounter_id}/terminate` | Terminate an active clinical intake encounter |

### Documents, OCR & Intelligence

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/documents/upload` | Upload PDF or image file (magic bytes & size validated, max 10MB) |
| `POST` | `/documents/{id}/ocr` | Run NVIDIA Nemotron OCR v2 on stored document pages |
| `POST` | `/documents/{id}/extract` | Extract structured observations, meds, allergies from OCR text |
| `GET` | `/documents/{id}/intelligence` | Generate deterministic timeline and reference range highlights |
| `GET` | `/patients/{id}/clinical-summary`| Compile structured clinical history summary for consultation |

### Physician Review & Consultations

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/patients/{id}/consultations` | Register an intake encounter into the physician review queue |
| `GET` | `/patients/physician/reviews` | Retrieve OPD consultation queue with status counts |
| `GET` | `/patients/{id}/physician-review-packet` | Retrieve source-backed review packet (consent enforced) |
| `POST` | `.../consultations/{cid}/review/notes` | Save attending physician clinical notes |
| `POST` | `.../consultations/{cid}/review/verify` | Record affirmative physician field verification |
| `POST` | `.../consultations/{cid}/review/complete` | Complete sign-off audit and lock consultation record |

### ABDM Sandbox Foundation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `PUT` | `/patients/{id}/abha` | Link and normalize 14-digit ABHA number locally |
| `POST` | `/patients/{id}/abdm/export` | Generate sandbox export bundle (requires active `abdm_sharing`) |

---

## 🧪 Testing & Verification

The codebase includes an extensive suite of automated tests and live integration checkpoints:

```powershell
# 1. Run full unit and integration test suite (86 passing tests)
$env:PYTHONPATH="."
pytest

# 2. Run live End-to-End verification against running FastAPI server
python scratch/verify_e2e.py

# 3. Test Groq Whisper + Groq GPT OSS 120B voice pipeline
python scratch/test_voice_pipeline.py

# 4. Test multi-language UI translation across all 5 languages
node scratch/test_ui_i18n.js
```

---

## 🛡️ Privacy, Ethics & Clinical Guardrails

- **No Self-Diagnosis**: MediKiosk strictly collects intake facts and explicitly advises patients to seek clinical attention if red flags (e.g. chest pain, breathing difficulty) are detected.
- **Physician Authority**: Automated extractions and summaries are prominently flagged as `NOT PHYSICIAN VERIFIED` until an authorized healthcare provider completes review and verification.
- **Granular Consent**: Informed consent is collected individually per purpose. Patients can revoke consent at any time from the kiosk.
- **Zero Token Leakage**: API credentials, tokens, and secrets are strictly stored in server environment variables and never exposed to client-side code.
