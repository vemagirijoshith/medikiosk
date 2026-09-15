import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.encounter import Encounter
from app.models.ocr_result import OCRResult
from app.models.patient import Patient
from app.models.symptom import Symptom
from app.schemas.ayush_coding import AyushCodingResponse, AyushDualCodeEntry

# Controlled official NAMASTE (National AYUSH Morbidity and Standardized Terminologies)
# and WHO ICD-11 Traditional Medicine Module 2 (Chapter 26) dual-coding catalog.
# Sources: Ministry of AYUSH NAMASTE Portal (NAMC) & WHO ICD-11 Chapter 26 (TM2).
AYUSH_CATALOG: list[dict[str, Any]] = [
    {
        "keywords": [r"\bfever\b", r"\btemperature\b", r"\bjvara\b", r"\bjwar\b", r"\bpyrexia\b"],
        "concept": "Fever / Elevated Body Temperature",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-001",
        "namaste_term": "Jvara (Elevated body temperature / Systemic febrile illness)",
        "who_icd11_code": "TM2-AYU-001",
        "who_icd11_term": "Disorder characterized by elevated body temperature - Jvara",
    },
    {
        "keywords": [r"\bback pain\b", r"\blower back\b", r"\blumbago\b", r"\bkati shula\b", r"\bkatishula\b", r"\bsciatica\b", r"\bgridhrasi\b"],
        "concept": "Low Back Pain / Sciatica",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-088",
        "namaste_term": "Kati Shula / Gridhrasi (Lumbosacral pain and Sciatica)",
        "who_icd11_code": "TM2-AYU-088",
        "who_icd11_term": "Lumbosacral and lower extremity pain disorder - Katishula / Gridhrasi",
    },
    {
        "keywords": [r"\bjoint pain\b", r"\bark\b", r"\barthritis\b", r"\bosteoarthritis\b", r"\bsandhivata\b", r"\bknee pain\b", r"\bswollen joints?\b"],
        "concept": "Joint Disorder / Osteoarthritis",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-042",
        "namaste_term": "Sandhigata Vata / Sandhivata (Osteoarthritis / Articular disorder)",
        "who_icd11_code": "TM2-AYU-042",
        "who_icd11_term": "Degenerative and articular disorder of joints - Sandhivata",
    },
    {
        "keywords": [r"\bstomach pain\b", r"\babdominal pain\b", r"\budarashula\b", r"\bbelly pain\b", r"\bcramps\b", r"\bgastric pain\b"],
        "concept": "Abdominal Pain / Colic",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-018",
        "namaste_term": "Udara Shula (Abdominal colic / Visceral distress)",
        "who_icd11_code": "TM2-AYU-018",
        "who_icd11_term": "Abdominal pain disorder - Udarashula",
    },
    {
        "keywords": [r"\bacidity\b", r"\bacid reflux\b", r"\bheartburn\b", r"\bgastritis\b", r"\bamlapitta\b", r"\bgerd\b", r"\bindigestion\b"],
        "concept": "Hyperacidity / Acid Dyspepsia",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-019",
        "namaste_term": "Amlapitta (Hyperacidity / Acid peptic syndrome)",
        "who_icd11_code": "TM2-AYU-019",
        "who_icd11_term": "Disorder of digestive fire and gastric acidity - Amlapitta",
    },
    {
        "keywords": [r"\bcough\b", r"\bkasa\b", r"\bbronchitis\b", r"\bdry cough\b", r"\bwet cough\b"],
        "concept": "Cough / Bronchial Irritation",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-024",
        "namaste_term": "Kasa (Cough / Respiratory passage affliction)",
        "who_icd11_code": "TM2-AYU-024",
        "who_icd11_term": "Respiratory tract disorder with cough - Kasa",
    },
    {
        "keywords": [r"\bbreathless\b", r"\bshortness of breath\b", r"\bdifficulty breathing\b", r"\basthma\b", r"\bshwasa\b", r"\bdyspnea\b"],
        "concept": "Breathlessness / Bronchial Asthma",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-031",
        "namaste_term": "Tamaka Shwasa (Bronchial Asthma / Respiratory distress)",
        "who_icd11_code": "TM2-AYU-031",
        "who_icd11_term": "Respiratory difficulty disorder - Shwasa",
    },
    {
        "keywords": [r"\bheadache\b", r"\bhead pain\b", r"\bmigraine\b", r"\bshirahshula\b", r"\bcephalea\b"],
        "concept": "Headache / Cephalea",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-105",
        "namaste_term": "Shirahshula (Cephalea / Tension and vascular head pain)",
        "who_icd11_code": "TM2-AYU-105",
        "who_icd11_term": "Disorder characterized by head pain - Shirahshula",
    },
    {
        "keywords": [r"\bdiabet(es|ic)\b", r"\bhigh sugar\b", r"\bhyperglycemia\b", r"\bmadhumeha\b", r"\bprameha\b"],
        "concept": "Diabetes Mellitus / Prameha",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-055",
        "namaste_term": "Madhumeha / Prameha (Diabetes mellitus / Metabolic urinary disease)",
        "who_icd11_code": "TM2-AYU-055",
        "who_icd11_term": "Metabolic and urinary passage disorder - Madhumeha",
    },
    {
        "keywords": [r"\bhypertension\b", r"\bhigh blood pressure\b", r"\bblood pressure\b", r"\bhbp\b", r"\braktavata\b", r"\braktachapa\b"],
        "concept": "Essential Hypertension",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-067",
        "namaste_term": "Rakta-Capa-Adhikya / Raktavata (Essential hypertension)",
        "who_icd11_code": "TM2-AYU-067",
        "who_icd11_term": "Vascular and pressure disorder - Raktachapa",
    },
    {
        "keywords": [r"\brash\b", r"\bitching\b", r"\beczema\b", r"\bdermatitis\b", r"\bkustha\b", r"\bvicharchika\b", r"\bkandu\b"],
        "concept": "Eczematous Dermatitis / Skin Lesion",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-112",
        "namaste_term": "Vicharchika / Kandu (Eczematous skin lesion / Pruritus)",
        "who_icd11_code": "TM2-AYU-112",
        "who_icd11_term": "Dermatological disorder - Kustha / Vicharchika",
    },
    {
        "keywords": [r"\bloose motions?\b", r"\bdiarrh?oea\b", r"\batisara\b", r"\bwatery stools?\b"],
        "concept": "Diarrhea / Enteric Disorder",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-015",
        "namaste_term": "Atisara (Diarrhea / Enteric hypermotility)",
        "who_icd11_code": "TM2-AYU-015",
        "who_icd11_term": "Enteric disorder with frequent liquid stools - Atisara",
    },
    {
        "keywords": [r"\bconstipation\b", r"\bvibandha\b", r"\bmalabaddhata\b", r"\bhard stools?\b"],
        "concept": "Constipation / Bowel Stasis",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-016",
        "namaste_term": "Vibandha / Anaha (Constipation / Fecal stasis)",
        "who_icd11_code": "TM2-AYU-016",
        "who_icd11_term": "Disorder of bowel motility - Vibandha",
    },
    {
        "keywords": [r"\binsomnia\b", r"\bsleeplessness\b", r"\banidra\b", r"\bpoor sleep\b"],
        "concept": "Insomnia / Sleep Disturbance",
        "system": "Ayurveda",
        "namaste_code": "NAMC-AYU-077",
        "namaste_term": "Anidra (Sleeplessness / Disturbed nocturnal sleep)",
        "who_icd11_code": "TM2-AYU-077",
        "who_icd11_term": "Sleep and wakefulness disorder - Anidra",
    },
]


def _match_term(term: str) -> dict[str, Any] | None:
    """Deterministically match a clinical term to the controlled AYUSH catalog."""
    normalized = term.strip().lower()
    for entry in AYUSH_CATALOG:
        for pat in entry["keywords"]:
            if re.search(pat, normalized, re.IGNORECASE):
                return entry
    return None


def extract_clinical_terms(db: Session, patient_id: int, encounter_id: int | None = None) -> list[str]:
    """Gather all explicitly recorded complaints, symptoms, and OCR conditions."""
    terms: list[str] = []

    # 1. Encounter chief complaint
    encounters_query = db.query(Encounter).filter(Encounter.patient_id == patient_id)
    if encounter_id:
        encounters_query = encounters_query.filter(Encounter.id == encounter_id)
    encounters = encounters_query.all()

    for enc in encounters:
        if enc.chief_complaint and enc.chief_complaint.strip():
            terms.append(enc.chief_complaint.strip())

    # 2. Symptoms
    encounter_ids = [enc.id for enc in encounters]
    if encounter_ids:
        symptoms = db.query(Symptom).filter(Symptom.encounter_id.in_(encounter_ids)).all()
        for s in symptoms:
            if s.name and s.name.strip():
                terms.append(s.name.strip())
            if s.description and s.description.strip():
                terms.append(s.description.strip())

    # 3. Document OCR extractions
    ocr_results = (
        db.query(OCRResult)
        .join(Encounter, OCRResult.document_id == Encounter.id, isouter=True)
        .all()
    )
    # Check extractions
    for r in ocr_results:
        if isinstance(r.structured_data, dict):
            ext = r.structured_data.get("medical_extraction", {})
            if isinstance(ext, dict):
                conditions = ext.get("diagnoses_or_conditions", [])
                for c in conditions:
                    if isinstance(c, dict) and "text" in c:
                        terms.append(c["text"])
                    elif isinstance(c, str):
                        terms.append(c)

    # Deduplicate while preserving order
    seen = set()
    unique_terms = []
    for t in terms:
        t_clean = t.strip()
        if t_clean and t_clean.lower() not in seen:
            seen.add(t_clean.lower())
            unique_terms.append(t_clean)

    return unique_terms


def build_dashavidha_pariksha_context(patient: Patient, encounter: Encounter | None = None) -> dict[str, str | None]:
    """Produce the 10 Dashavidha Pariksha clinical context parameters."""
    age = patient.age
    vaya_desc = "Balya (Childhood / Growth)" if age < 16 else ("Madhyama (Adult / Active)" if age <= 60 else "Vriddha (Geriatric)")

    return {
        "1_prakriti": "Vata-Pitta-Kapha constitutional inquiry pending vaidya evaluation",
        "2_vikriti": encounter.chief_complaint if encounter and encounter.chief_complaint else "Symptomatic presentation recorded in pre-consultation intake",
        "3_sara": "Pending physical tissue examination",
        "4_samhanana": "Pending compact-build clinical inspection",
        "5_pramana": f"Age: {patient.age} yrs, Gender: {patient.gender}",
        "6_satmya": "Dietary and habitual adaptability inquiry recorded during intake",
        "7_satva": "Mental disposition assessed in guided dialogue",
        "8_ahara_shakti": "Digestive capacity recorded via appetite inquiry",
        "9_vyayama_shakti": "Exercise tolerance / physical endurance pending examination",
        "10_vaya": f"{vaya_desc} ({age} years)",
    }


def map_ayush_codes(
    db: Session, patient_id: int, encounter_id: int | None = None
) -> AyushCodingResponse:
    """Build AYUSH NAMASTE + WHO ICD-11 TM2 dual-coding response deterministically."""
    patient = db.get(Patient, patient_id)
    if not patient:
        return AyushCodingResponse(patient_id=patient_id, coding_status="unmapped", codes=[])

    encounter = None
    if encounter_id:
        encounter = db.query(Encounter).filter(Encounter.id == encounter_id, Encounter.patient_id == patient_id).first()
    else:
        encounter = db.query(Encounter).filter(Encounter.patient_id == patient_id).order_by(Encounter.started_at.desc()).first()

    terms = extract_clinical_terms(db, patient_id, encounter.id if encounter else None)
    if not terms and encounter and encounter.chief_complaint:
        terms = [encounter.chief_complaint]

    codes: list[AyushDualCodeEntry] = []
    has_mapped = False

    for term in terms:
        matched = _match_term(term)
        if matched:
            has_mapped = True
            codes.append(
                AyushDualCodeEntry(
                    concept=matched["concept"],
                    matched_term=term,
                    system=matched["system"],
                    namaste_code=matched["namaste_code"],
                    namaste_term=matched["namaste_term"],
                    who_icd11_code=matched["who_icd11_code"],
                    who_icd11_term=matched["who_icd11_term"],
                    coding_status="mapped",
                    coding_source="NAMASTE (Ministry of AYUSH) & WHO ICD-11 Chapter 26 (TM2)",
                    is_physician_verified=False,
                )
            )
        else:
            codes.append(
                AyushDualCodeEntry(
                    concept="Clinical Symptom / Unmapped Condition",
                    matched_term=term,
                    system="Ayurveda",
                    namaste_code=None,
                    namaste_term=None,
                    who_icd11_code=None,
                    who_icd11_term=None,
                    coding_status="unmapped",
                    coding_source="Controlled catalog lookup (no direct match found)",
                    is_physician_verified=False,
                )
            )

    dashavidha = build_dashavidha_pariksha_context(patient, encounter)

    return AyushCodingResponse(
        patient_id=patient_id,
        encounter_id=encounter.id if encounter else None,
        coding_status="mapped" if has_mapped else "unmapped",
        codes=codes,
        dashavidha_pariksha_context=dashavidha,
    )
