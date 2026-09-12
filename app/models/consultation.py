from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[int] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescription: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient = relationship("Patient", back_populates="consultations")
    encounter = relationship("Encounter", back_populates="consultations")