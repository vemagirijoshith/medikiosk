from pydantic import BaseModel, ConfigDict, Field


class AyushDualCodeEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept: str
    matched_term: str
    system: str = "Ayurveda"
    namaste_code: str | None = None
    namaste_term: str | None = None
    who_icd11_code: str | None = None
    who_icd11_term: str | None = None
    coding_status: str = Field(
        ..., description="'mapped' if an official catalog code was matched, otherwise 'unmapped'"
    )
    coding_source: str = "NAMASTE (Ministry of AYUSH) & WHO ICD-11 Chapter 26 (TM2)"
    is_physician_verified: bool = False


class AyushCodingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    encounter_id: int | None = None
    coding_status: str = "mapped"
    codes: list[AyushDualCodeEntry] = []
    dashavidha_pariksha_context: dict[str, str | None] = {}
    disclaimer: str = (
        "AUTOMATED AYUSH DUAL-CODING (NAMASTE + WHO ICD-11 TM2) — NOT PHYSICIAN VERIFIED. "
        "Strictly deterministic ontology mapping without artificial intelligence code generation."
    )
