import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_document_upload_columns():
    inspector = inspect(engine)
    if not inspector.has_table("documents"):
        return
    existing_columns = {
        column["name"] for column in inspector.get_columns("documents")
    }
    additions = {
        "encounter_id": 'ALTER TABLE documents ADD COLUMN encounter_id INTEGER REFERENCES encounters(id) ON DELETE SET NULL',
        "content_type": "ALTER TABLE documents ADD COLUMN content_type VARCHAR(100) NOT NULL DEFAULT 'application/octet-stream'",
        "file_size": "ALTER TABLE documents ADD COLUMN file_size BIGINT NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        for column_name, statement in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def ensure_consent_columns():
    inspector = inspect(engine)
    if not inspector.has_table("consents"):
        return
    existing_columns = {column["name"] for column in inspector.get_columns("consents")}
    additions = {
        "status": "ALTER TABLE consents ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'granted'",
        "revoked_at": "ALTER TABLE consents ADD COLUMN revoked_at TIMESTAMP",
        "source": "ALTER TABLE consents ADD COLUMN source VARCHAR(50)",
        "metadata": "ALTER TABLE consents ADD COLUMN metadata TEXT",
    }
    with engine.begin() as connection:
        for column_name, statement in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        if "granted" in existing_columns:
            connection.execute(
                text("UPDATE consents SET status = 'revoked' WHERE granted = 0 AND status = 'granted'")
            )


def ensure_patient_abha_index():
    inspector = inspect(engine)
    if not inspector.has_table("patients"):
        return
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_patients_abha_id ON patients (abha_id)"
        ))


def ensure_physician_review_columns():
    """Add D3 fields without altering existing consultation data."""
    inspector = inspect(engine)
    if not inspector.has_table("consultations"):
        return
    existing_columns = {column["name"] for column in inspector.get_columns("consultations")}
    additions = {
        "review_status": "ALTER TABLE consultations ADD COLUMN review_status VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "physician_id": "ALTER TABLE consultations ADD COLUMN physician_id VARCHAR(255)",
        "physician_notes": "ALTER TABLE consultations ADD COLUMN physician_notes TEXT",
        "reviewed_at": "ALTER TABLE consultations ADD COLUMN reviewed_at TIMESTAMP",
    }
    with engine.begin() as connection:
        for column_name, statement in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


def ensure_queue_priority_columns():
    """Ensure priority and red_flag_reason columns exist on encounters and consultations."""
    inspector = inspect(engine)
    with engine.begin() as connection:
        if inspector.has_table("encounters"):
            encounter_cols = {col["name"] for col in inspector.get_columns("encounters")}
            if "priority" not in encounter_cols:
                connection.execute(text("ALTER TABLE encounters ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'routine'"))
            if "red_flag_reason" not in encounter_cols:
                connection.execute(text("ALTER TABLE encounters ADD COLUMN red_flag_reason TEXT"))
        if inspector.has_table("consultations"):
            consult_cols = {col["name"] for col in inspector.get_columns("consultations")}
            if "priority" not in consult_cols:
                connection.execute(text("ALTER TABLE consultations ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'routine'"))
            if "red_flag_reason" not in consult_cols:
                connection.execute(text("ALTER TABLE consultations ADD COLUMN red_flag_reason TEXT"))


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

