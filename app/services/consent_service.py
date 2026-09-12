from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.consent import Consent, ConsentStatus


def has_active_consent(
    db: Session,
    patient_id: int,
    purpose: str
) -> bool:
    """
    Check if a patient has active consent for a specific purpose.
    
    Returns True only if there is an active (granted, not revoked/expired) consent record.
    """
    consent = db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.purpose == purpose,
        Consent.status == ConsentStatus.GRANTED.value,
        Consent.granted.is_(True)
    ).first()
    
    return consent is not None


def get_consent(
    db: Session,
    patient_id: int,
    purpose: str
) -> Optional[Consent]:
    """Get the latest consent record for a patient and purpose."""
    return db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.purpose == purpose
    ).order_by(Consent.created_at.desc()).first()


def get_all_consents(
    db: Session,
    patient_id: int
) -> list[Consent]:
    """Get all consent records for a patient."""
    return db.query(Consent).filter(
        Consent.patient_id == patient_id
    ).order_by(Consent.created_at.desc()).all()


def grant_consent(
    db: Session,
    patient_id: int,
    purpose: str,
    consent_version: str,
    source: str | None = None,
    metadata: str | None = None
) -> Consent:
    """
    Grant consent for a specific purpose.
    
    If an existing consent for the same purpose exists, it will be revoked
    and a new one will be created.
    """
    # Revoke any existing active consent for this purpose
    existing = db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.purpose == purpose,
        Consent.status == ConsentStatus.GRANTED.value,
        Consent.granted.is_(True)
    ).first()
    
    if existing:
        existing.status = ConsentStatus.REVOKED.value
        existing.granted = False
        existing.revoked_at = datetime.now()
    
    # Create new consent record
    consent = Consent(
        patient_id=patient_id,
        purpose=purpose,
        status=ConsentStatus.GRANTED.value,
        granted=True,
        consent_version=consent_version,
        source=source,
        audit_metadata=metadata
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def revoke_consent(
    db: Session,
    patient_id: int,
    purpose: str,
    reason: str | None = None
) -> Optional[Consent]:
    """
    Revoke consent for a specific purpose.
    
    Does not delete the historical record, just marks it as revoked.
    """
    consent = db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.purpose == purpose,
        Consent.status == ConsentStatus.GRANTED.value,
        Consent.granted.is_(True)
    ).first()
    
    if not consent:
        return None
    
    consent.status = ConsentStatus.REVOKED.value
    consent.granted = False
    consent.revoked_at = datetime.now()
    if reason:
        consent.audit_metadata = (consent.audit_metadata or "") + f"\nRevoked: {reason}"
    
    db.commit()
    db.refresh(consent)
    return consent


def get_consent_history(
    db: Session,
    patient_id: int,
    purpose: str
) -> list[Consent]:
    """Get all consent records for a specific purpose (including revoked/expired)."""
    return db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.purpose == purpose
    ).order_by(Consent.created_at.desc()).all()