from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ABDMShareAudit(Base):
    __tablename__ = "abdm_share_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[int | None] = mapped_column(
        ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    consent_id: Mapped[int | None] = mapped_column(
        ForeignKey("consents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    audit_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )

    patient = relationship("Patient")
    encounter = relationship("Encounter")
    consent = relationship("Consent")
