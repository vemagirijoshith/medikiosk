from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="in_progress"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="routine", server_default="routine"
    )
    red_flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    patient = relationship("Patient", back_populates="encounters")
    symptoms = relationship(
        "Symptom", back_populates="encounter", cascade="all, delete-orphan"
    )
    consultations = relationship("Consultation", back_populates="encounter")
    documents = relationship("Document", back_populates="encounter")