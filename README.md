# MediKiosk Backend

FastAPI backend for the MediKiosk clinical history prototype.

## Run locally

1. Start PostgreSQL and ensure the existing `DATABASE_URL` in `.env` points to it.
2. Ensure NVIDIA API access is available.
3. Configure `.env` without committing it:

```dotenv
DATABASE_URL=postgresql://...
NVIDIA_API_KEY=your-local-nvidia-key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_OCR_BASE_URL=https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2
NVIDIA_OCR_MODEL=nvidia/nemotron-ocr-v2
```

4. Start FastAPI from the project directory:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001
```

The API is available at `http://127.0.0.1:8001`. Swagger is at `/docs`.

## Clinical intake flow

Create or use a patient, then start an intake session:

```http
POST /intake/start
Content-Type: application/json

{
  "patient_id": 1,
  "language": "en",
  "mode": "general"
}
```

Continue the session with the returned encounter ID:

```http
POST /intake/message
Content-Type: application/json

{
  "encounter_id": 1,
  "message": "I have stomach pain."
}
```

The intake API keeps active conversation context in the backend process and
persists extracted chief complaint and symptom details through the existing
Encounter and Symptom models. The AI service only accepts OpenAI-compatible
chat completions and never logs or returns the API key.

## Endpoints

- `GET /`: health response
- `POST /patients/`: create a patient
- `GET /patients/{patient_id}`: retrieve a patient
- `POST /intake/start`: start a clinical history session
- `POST /intake/message`: continue a clinical history session
- `POST /intake/{encounter_id}/terminate`: terminate an active intake session
- `POST /documents/upload`: upload a validated PDF, JPEG, JPG, or PNG document
- `POST /documents/{document_id}/ocr`: process stored document pages with Nemotron OCR v2
- `POST /documents/{document_id}/extract`: extract explicitly stated medical information from OCR text
- `GET /documents/{document_id}/intelligence`: build deterministic timeline and reference-range highlights
- `GET /patients/{patient_id}/clinical-summary`: generate a physician-facing clinical history summary
- `POST /patients/{patient_id}/consents`: grant purpose-specific consent
- `GET /patients/{patient_id}/consents`: retrieve consent history
- `GET /patients/{patient_id}/consents/check`: check active consent for a purpose
- `POST /patients/{patient_id}/consents/{consent_id}/revoke`: revoke consent
- `GET /docs`: Swagger UI

### D1 consent and privacy

Consent is purpose-specific: `clinical_history`, `document_processing`,
`document_extraction`, `clinical_summary`, `physician_review`, and
`abdm_sharing`. Grants create auditable records; revocation preserves the
historical row and immediately makes the purpose inactive. The reusable
consent service never treats missing, revoked, or expired consent as active.

Existing development workflows do not yet require consent by default, so the
current 58-test fixture-compatible APIs continue to work. The safe integration
points are the clinical history, document processing/extraction, and clinical
summary boundaries. Future ABDM sharing must check `abdm_sharing` explicitly.
ABHA authentication and ABDM API integration are not implemented yet.

### D2 ABDM/ABHA integration foundation

ABHA linking is local and sandbox-ready only. `PUT
/patients/{patient_id}/abha` stores a normalized 14-digit identifier and does
not claim ABDM verification. `POST /patients/{patient_id}/abdm/export` requires
active `abdm_sharing` consent, builds an export from existing structured
MediKiosk data, and records an audit event. With `ABDM_SANDBOX_MODE=true`, the
response is `sandbox_ready`; no real ABDM transmission or fake production API
call is made. Client secrets, tokens, OTPs, Aadhaar numbers, and credentials
are never stored or returned.

The D2 service boundary is ready for a future official ABDM sandbox adapter.
Official ABDM contracts and sandbox credentials must be obtained before adding
external network calls.

### D2 ABDM/ABHA foundation

ABHA linking is currently local and sandbox-ready only. `PUT
/patients/{patient_id}/abha` stores a conservatively normalized ABHA identifier;
it does not verify the identifier with ABDM. `POST
/patients/{patient_id}/abdm/export` requires active `abdm_sharing` consent and
builds a structured export from existing MediKiosk records. With
`ABDM_SANDBOX_MODE=true`, it returns `sandbox_ready` and does not transmit data
to ABDM. No fake ABDM endpoints or network calls are made.

Configure `ABDM_BASE_URL`, `ABDM_CLIENT_ID`, `ABDM_CLIENT_SECRET`, and
`ABDM_SANDBOX_MODE` through environment variables only. Official ABDM sandbox
credentials and documented API contracts are required before adding an actual
external connector. Export attempts are recorded in `abdm_share_audits` without
storing secrets, tokens, OTPs, or Aadhaar numbers.

Document uploads accept multipart form data with `patient_id`, an optional
`encounter_id`, and `file`. Files are limited to 10 MB, checked by MIME type
and magic bytes, stored under a UUID-based name in `storage/documents/`, and
persisted as metadata only. OCR is not performed by this endpoint.

OCR is an explicit second stage. The OCR service sends each image page to
`POST https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2/v1/ocr` using a
JSON payload with an `input` array containing an `image_url` data URL. PDFs are
rendered to PNG pages before submission. OCR results are stored in the existing
`OCRResult` table and no clinical interpretation is performed.

### B5 medical extraction

After OCR completes, `/documents/{document_id}/extract` sends only the stored
OCR text to the existing NVIDIA Nemotron 3 Ultra chat service. The response is
validated with a strict Pydantic schema and stored under
`OCRResult.structured_data.medical_extraction`; the original normalized OCR
data remains unchanged. Extraction preserves `source_text` for physician
verification and never diagnoses, interprets, or recommends treatment.

### B6 document intelligence

The B6 endpoint deterministically organizes existing B5 data for physician
review. It sorts explicitly dated document events, keeps undated events without
inventing dates, and highlights observations as `low`, `normal`, `high`, or
`unknown` only when the source document provides a usable reference range.
Compound values such as blood pressure remain `unknown` unless safely
parseable. B6 makes no NVIDIA calls, adds no tables, and does not diagnose or
recommend treatment.

### Module C structured clinical history summary

Module C combines existing Patient, Encounter, Symptom, Medication, Allergy,
OCRResult/B5, and B6 data for physician review. It assembles source facts
deterministically, asks Nemotron 3 Ultra only to organize those supplied facts,
validates the JSON response, and rejects unsupported medications, allergies,
diagnoses, dates, and document IDs. The generated summary is returned without
overwriting source records; source text and document IDs remain traceable. It
does not diagnose, prescribe, recommend treatment, or provide medical advice.

## Current provider limitation

The clinical history engine uses NVIDIA's OpenAI-compatible API with
`nvidia/nemotron-3-ultra-550b-a55b`. The backend still starts normally if the
provider is unavailable. Intake messages translate provider rate limits into
HTTP 503 with a safe retry message; provider credentials and internal upstream
details are not exposed.