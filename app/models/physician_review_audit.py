from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, event, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PhysicianReviewAudit(Base):
    """Append-only provenance for D3 review actions; metadata contains IDs only."""

    __tablename__ = "physician_review_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    consultation_id: Mapped[int | None] = mapped_column(ForeignKey("consultations.id", ondelete="SET NULL"), nullable=True, index=True)
    # This is supplied externally and is never authentication evidence.
    physician_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    audit_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )


def _prevent_audit_mutation(*_args: Any, **_kwargs: Any) -> None:
    raise ValueError("Physician review audit records are immutable")


event.listen(PhysicianReviewAudit, "before_update", _prevent_audit_mutation)
event.listen(PhysicianReviewAudit, "before_delete", _prevent_audit_mutation)
