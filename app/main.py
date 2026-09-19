import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
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

_log = logging.getLogger("medikiosk.keepalive")

# ── Keep-alive: prevent Render free-tier sleep ────────────────────────────────
# Render spins down free services after ~15 min of inactivity.
# This background task pings the service's own /healthz every 10 minutes so
# Render always sees traffic and never sleeps.
SELF_URL = os.environ.get(
    "RENDER_EXTERNAL_URL",          # Render injects this automatically
    "https://medikiosk-yri0.onrender.com",  # hard-coded fallback
)
KEEPALIVE_INTERVAL = 10 * 60  # 10 minutes — inside Render's 15-min sleep window


async def _keepalive_loop():
    """Ping own /healthz every 10 min so Render never goes to sleep."""
    await asyncio.sleep(30)  # let the server fully start before first ping
    while True:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(f"{SELF_URL}/healthz")
                _log.info("Keep-alive ping → %s  status=%s", SELF_URL, r.status_code)
        except Exception as exc:
            _log.warning("Keep-alive ping failed (will retry): %s", exc)
        await asyncio.sleep(KEEPALIVE_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    try:
        ensure_document_upload_columns()
        ensure_consent_columns()
        ensure_physician_review_columns()
        ensure_queue_priority_columns()
        Base.metadata.create_all(bind=engine)
        ensure_patient_abha_index()
    except Exception as exc:
        _log.warning("Database schema auto-init deferred: %s", exc)

    task = asyncio.create_task(_keepalive_loop())
    _log.info("Keep-alive task started — pinging %s every %ds", SELF_URL, KEEPALIVE_INTERVAL)

    yield  # ── server is running ──────────────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────────────────
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="MediKiosk API",
    description="AI-powered Clinical History Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production Vercel frontend
        "https://medikiosk-ebon.vercel.app",
        # Local development origins
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    # NOTE: allow_origin_regex is intentionally NOT used here.
    # Combining allow_origin_regex with allow_credentials=True can cause
    # Starlette to silently omit Access-Control-Allow-Origin on some
    # preflight paths. Use explicit origins only.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(patient_router)
app.include_router(intake_router)
app.include_router(documents_router)
app.include_router(clinical_summary_router)
app.include_router(consent_router)
app.include_router(abdm_router)
app.include_router(physician_review_router)

# ── Health & root routes MUST be registered BEFORE StaticFiles mount ─────────
# Starlette's StaticFiles is a sub-application that catches any unmatched path.
# If it were mounted first, requests to /healthz could be intercepted and return
# 404 instead of the JSON response, making the service appear offline.

@app.get("/healthz")
def healthz():
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={"status": "ok"},
        headers={
            # Prevent CDNs, proxies, and mobile browsers from caching the
            # health response — always fetch fresh from Render.
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        }
    )


@app.get("/")
def root():
    return {
        "message": "MediKiosk Backend is running 🚀"
    }


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/kiosk", StaticFiles(directory=frontend_dir, html=True), name="kiosk")
