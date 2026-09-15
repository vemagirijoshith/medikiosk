/**
 * MediKiosk - Smart Clinical Intake & Patient Care Platform
 * Frontend Architecture & API Integration Layer
 */

const API_BASE = window.location.origin.includes(':8001') ? '' : 'http://127.0.0.1:8001';
const API_TIMEOUT = 35000;

const PURPOSES = [
  {
    key: "clinical_history",
    title: "Clinical History Intake",
    desc: "Collect and structure your symptoms and medical history for this visit.",
    requiredForIntake: true,
  },
  {
    key: "document_processing",
    title: "Medical Document Processing",
    desc: "Securely store and perform optical character recognition (OCR) on your uploaded medical files.",
    requiredForIntake: false,
  },
  {
    key: "document_extraction",
    title: "Structured Medical Extraction",
    desc: "Extract explicitly written lab observations, medications, and allergies from OCR text.",
    requiredForIntake: false,
  },
  {
    key: "clinical_summary",
    title: "Clinical Visit Summary",
    desc: "Compile all collected facts and documents into a physician-facing history summary.",
    requiredForIntake: false,
  },
  {
    key: "physician_review",
    title: "Physician Review Access",
    desc: "Grant your attending medical team permission to access and review your intake packet.",
    requiredForIntake: false,
  },
  {
    key: "abdm_sharing",
    title: "ABDM Health Record Sharing",
    desc: "Ayushman Bharat Digital Mission sandbox sharing. Optional and strictly separated from in-clinic care.",
    isAbdm: true,
    requiredForIntake: false,
  },
];

const LANGUAGES = [
  // Tier 1: Fully Localized Kiosk UI + Voice Assisted
  { code: "en", label: "English", native: "English", sub: "Primary kiosk language", tier: "full" },
  { code: "hi", label: "Hindi", native: "हिन्दी", sub: "हिंदी में जारी रखें", tier: "full" },
  { code: "te", label: "Telugu", native: "తెలుగు", sub: "తెలుగులో కొనసాగించండి", tier: "full" },
  { code: "ta", label: "Tamil", native: "தமிழ்", sub: "தமிழில் தொடரவும்", tier: "full" },
  { code: "bn", label: "Bengali", native: "বাংলা", sub: "বাংলায় চালিয়ে যান", tier: "full" },

  // Tier 2: 17 Scheduled Languages of India — Speech Assisted (Groq Whisper)
  { code: "mr", label: "Marathi", native: "मराठी", sub: "मराठीत बोला (Speech Assisted)", tier: "speech" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી", sub: "ગુજરાતીમાં બોલો (Speech Assisted)", tier: "speech" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ", sub: "ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ (Speech Assisted)", tier: "speech" },
  { code: "ml", label: "Malayalam", native: "മലയാളം", sub: "മലയാളത്തിൽ സംസാരിക്കുക (Speech Assisted)", tier: "speech" },
  { code: "pa", label: "Punjabi", native: "ਪੰਜਾਬੀ", sub: "ਪੰਜਾਬੀ ਵਿੱਚ ਬੋਲੋ (Speech Assisted)", tier: "speech" },
  { code: "or", label: "Odia", native: "ଓଡ଼ିଆ", sub: "ଓଡ଼ିଆରେ କୁహନ୍ତు (Speech Assisted)", tier: "speech" },
  { code: "as", label: "Assamese", native: "অসমীয়া", sub: "অসমীয়াত কওক (Speech Assisted)", tier: "speech" },
  { code: "ur", label: "Urdu", native: "اردو", sub: "اردو میں بولیں (Speech Assisted)", tier: "speech" },
  { code: "sa", label: "Sanskrit", native: "संस्कृतम्", sub: "संस्कृतेन वदतु (Speech Assisted)", tier: "speech" },
  { code: "mai", label: "Maithili", native: "मैथिली", sub: "मैथिली में बाजु (Speech Assisted)", tier: "speech" },
  { code: "sat", label: "Santali", native: "ᱥᱟᱱᱛᱟᱲᱤ", sub: "ᱥᱟᱱᱛᱟᱲᱤᱛᱮ ᱨᱚᱲ (Speech Assisted)", tier: "speech" },
  { code: "ks", label: "Kashmiri", native: "کٲشُر", sub: "کٲشُر بولِو (Speech Assisted)", tier: "speech" },
  { code: "ne", label: "Nepali", native: "नेपाली", sub: "नेपालीमा बोल्नुहोस् (Speech Assisted)", tier: "speech" },
  { code: "sd", label: "Sindhi", native: "سنڌي", sub: "سنڌيءَ ۾ ڳالهايو (Speech Assisted)", tier: "speech" },
  { code: "kok", label: "Konkani", native: "कोंकणी", sub: "कोंकणींत उलययात (Speech Assisted)", tier: "speech" },
  { code: "doi", label: "Dogri", native: "डोगरी", sub: "डोगरी च गल्ल करो (Speech Assisted)", tier: "speech" },
  { code: "brx", label: "Bodo", native: "बड़ो", sub: "बड़ो राव (Speech Assisted)", tier: "speech" },
  { code: "mni", label: "Manipuri", native: "মৈতৈলোন্", sub: "মৈতৈলোন (Speech Assisted)", tier: "speech" },
];

const I18N = {
  en: {
    selected_badge: "Selected ✓",
    staff_dialog_title: "Staff Assistance Requested",
    staff_dialog_desc: "Please remain at the kiosk. A hospital staff member is being alerted to your kiosk station.",
    staff_dialog_btn: "I Understand",
    upload_file_btn: "Upload File Now",
    uploaded_docs_title: "Uploaded Documents in this Visit",
    no_docs_uploaded: "No documents uploaded yet. You can upload a lab test report, or continue without one.",
    back_to_docs: "← Back to Documents",
    review_submit_visit: "Review & Submit Visit →",
    abha_abdm_sharing: "ABHA & ABDM Sharing",
    summary_hpi_title: "History of Present Illness (HPI)",
    summary_symptoms_title: "Reported Symptoms & Red Flags",
    summary_meds_allergies_title: "Prescriptions & Allergies",
    medications_lbl: "Medications:",
    allergies_lbl: "Allergies:",
    source_doc_findings_title: "Source Document Findings",
    review_eyebrow: "FINAL VERIFICATION BEFORE SUBMISSION",
    review_title: "Review Your Visit Information",
    review_subtitle: "Please ensure the information below is accurate before submitting to the physician queue.",
    patient_demographics: "👤 Patient Demographics",
    visit_overview: "📋 Visit & Consent Overview",
    affirmation_lbl: "Affirmation:",
    affirmation_note: "By clicking Submit, your structured intake information will be prepared as an official consultation record for the attending healthcare professional.",
    back_to_summary: "← Back to Summary",
    submit_final_visit_btn: "✓ Submit for Physician Review",
    success_eyebrow: "SUBMISSION COMPLETE",
    success_title: "Information Submitted Successfully",
    success_subtitle: "Your intake records have been securely registered and transferred to the outpatient clinical team.",
    visit_details_title: "Your Visit Details",
    consultation_record_lbl: "Consultation Record:",
    status_lbl: "Status:",
    pending_review_status: "Pending Physician Review",
    finish_kiosk_btn: "Finish & Return to Kiosk Home",
    sih_tag: "SIH 2026 Patient Caretaking",
    portal_btn: "👨‍⚕️ Physician Review",
    call_staff: "🚨 Call Staff",

    step_language: "Language",
    step_identity: "Identity",
    step_consent: "Consent",
    step_intake: "History Intake",
    step_documents: "Documents & OCR",
    step_review: "Review & Submit",

    welcome_eyebrow: "Smart India Hackathon 2026 · Healthcare Kiosk",
    welcome_title: "Welcome to MediKiosk",
    welcome_subtitle: "An AI-assisted, self-service clinical intake platform designed for fast, accurate, and dignified patient care in hospital outpatient departments.",
    start_touch: "Start Check-In (Touch / Text) →",
    start_voice: "🎙️ Start with Voice",
    privacy_title: "Strict Patient Privacy & Consent Guardrails",
    privacy_desc: "All information collected stays within the local hospital system. Automated extractions are unverified until explicitly reviewed and signed by an attending physician.",
    kiosk_self_service: "PATIENT SELF-SERVICE",
    self_service_title: "Self-Service Kiosk Intake",
    self_service_desc: "Register or look up your visit, grant explicit consent for each purpose, answer guided questions by voice or touch, and scan recent medical reports.",
    select_lang_begin: "Select Language & Begin",
    physician_team: "PHYSICIAN & CLINICAL TEAM",
    open_physician_workspace: "Open Physician Workspace →",

    lang_eyebrow: "STEP 1 OF 6",
    lang_title: "Choose Your Preferred Language",
    lang_subtitle: "You can speak and read in your preferred regional language throughout this kiosk session.",
    back_to_welcome: "← Back to Welcome",
    continue_to_identity: "Continue to Patient Identification →",

    id_eyebrow: "STEP 2 OF 6 · PATIENT IDENTIFICATION",
    id_title: "Identify or Register Patient",
    id_subtitle: "Enter your existing MediKiosk Patient ID, or register as a new patient for today's visit.",
    returning_patient: "RETURNING PATIENT",
    have_patient_id: "I have a Patient ID",
    returning_desc: "If you have previously registered at this kiosk, enter your ID below.",
    patient_id_input_label: "Patient ID",
    lookup_record_btn: "Look Up Record →",
    new_patient_reg: "NEW PATIENT REGISTRATION",
    first_time_title: "First Time at this Kiosk",
    first_time_desc: "Please provide basic details to create a secure visit encounter.",
    full_name: "Full Name",
    age: "Age",
    gender: "Gender",
    gender_female: "Female",
    gender_male: "Male",
    gender_other: "Other",
    gender_unspecified: "Prefer not to say",
    mobile_number: "Phone Number",
    abha_number: "ABHA ID / Ayushman Bharat ID",
    create_patient_btn: "Create Patient & Continue →",
    back_to_language: "← Back to Language",

    consent_eyebrow: "STEP 3 OF 6 · INFORMED CONSENT",
    consent_title: "Consent for Medical Information Use",
    consent_subtitle: "In accordance with healthcare ethics, each consent purpose is managed independently. You may grant or revoke consent at any time.",
    status_active: "Active (Granted)",
    status_not_granted: "Not Granted",
    status_revoked: "Revoked",
    grant_consent_btn: "✓ Grant Consent",
    revoke_consent_btn: "✕ Revoke Consent",
    change_patient_btn: "← Change Patient",
    save_start_intake_btn: "Save & Start Clinical Intake →",

    purpose_clinical_history_title: "Clinical History Intake",
    purpose_clinical_history_desc: "Collect and structure your symptoms and medical history for this visit.",
    purpose_document_processing_title: "Medical Document Processing",
    purpose_document_processing_desc: "Securely store and perform optical character recognition (OCR) on your uploaded medical files.",
    purpose_document_extraction_title: "Structured Medical Extraction",
    purpose_document_extraction_desc: "Extract explicitly written lab observations, medications, and allergies from OCR text.",
    purpose_clinical_summary_title: "Clinical Visit Summary",
    purpose_clinical_summary_desc: "Compile all collected facts and documents into a physician-facing history summary.",
    purpose_physician_review_title: "Physician Review Access",
    purpose_physician_review_desc: "Grant your attending medical team permission to access and review your intake packet.",
    purpose_abdm_sharing_title: "ABDM Health Record Sharing",
    purpose_abdm_sharing_desc: "Ayushman Bharat Digital Mission sandbox sharing. Optional and strictly separated from in-clinic care.",

    intake_eyebrow: "STEP 4 OF 6 · GUIDED HISTORY",
    hello_prefix: "Hello",
    intake_inst: "Answer one question at a time. You may speak using the microphone or type below.",
    whisper_pill: "🎙️ Groq Whisper Transcript",
    patient_review_badge: "Patient Review Required",
    whisper_confirm_hint: "Please verify or edit before sending to Groq GPT OSS 120B:",
    rerecord_btn: "🔄 Re-record",
    confirm_send_btn: "✓ Confirm & Send to AI →",
    chat_placeholder: "Type your response here, or click 'Speak' to record your voice...",
    speak_mic: "🎙️ Speak (Microphone)",
    stop_recording: "⏹️ Stop Recording",
    send_answer: "Send Answer →",
    urgent_banner_title: "Please Get Assistance Immediately",
    urgent_banner_desc: "A potentially urgent symptom was reported. A healthcare professional should evaluate your condition without delay. MediKiosk is an intake aid and cannot provide medical diagnosis.",
    call_staff_to_kiosk: "Call Staff to Kiosk",
    safety_notice_title: "⚠️ Patient Safety Notice",
    safety_notice_desc: "If at any point you feel severe chest pain, sudden breathlessness, uncontrollable bleeding, or severe dizziness, press Call Staff or inform nearby nurses immediately.",
    session_details: "VISIT SESSION DETAILS",
    patient_lbl: "Patient:",
    patient_id_lbl: "Patient ID:",
    encounter_id_lbl: "Encounter ID:",
    language_lbl: "Language:",
    consent_status_lbl: "Consent Status:",
    back_to_consent: "← Back to Consent",
    proceed_to_docs: "Proceed to Medical Documents →",

    doc_eyebrow: "STEP 5 OF 6 · MEDICAL DOCUMENTS & OCR",
    doc_title: "Upload Reports or Prescriptions",
    doc_subtitle: "Upload laboratory test results, discharge summaries, or previous prescriptions. Supported: PDF, JPG, JPEG, PNG (Max 10 MB).",
    dropzone_main: "Select or drop a medical document here",
    dropzone_sub: "Click to browse files on this device",
    run_ocr: "🔍 Run Nemotron OCR",
    extract_intel: "Extract Medical Intelligence →",
    back_to_intake: "← Back to Intake",
    proceed_to_summary: "Proceed to Clinical Summary →",

    summary_eyebrow: "STEP 6 OF 6 · VISIT COMPILATION",
    summary_title: "Comprehensive Clinical Summary",
    submit_consultation: "Submit for Physician Consultation →",
  },

  te: {
    selected_badge: "ఎంచుకోబడింది ✓",
    staff_dialog_title: "సిబ్బంది సహాయం అభ్యర్థించబడింది",
    staff_dialog_desc: "దయచేసి కియోస్క్ వద్ద ఉండండి. ఆసుపత్రి సిబ్బంది మీ కియోస్క్ స్టేషన్‌కు వస్తున్నారు.",
    staff_dialog_btn: "నాకు అర్థమైంది",
    upload_file_btn: "ఫైల్‌ను ఇప్పుడే అప్‌లోడ్ చేయండి",
    uploaded_docs_title: "ఈ సందర్శనలో అప్‌లోడ్ చేసిన పత్రాలు",
    no_docs_uploaded: "ఇంకా పత్రాలు ఏవీ అప్‌లోడ్ చేయలేదు. మీరు ల్యాబ్ పరీక్ష నివేదికను అప్‌లోడ్ చేయవచ్చు లేదా లేకుండా కొనసాగవచ్చు.",
    back_to_docs: "← పత్రాలకు తిరిగి వెళ్లండి",
    review_submit_visit: "సమీక్షించి సందర్శనను సమర్పించండి →",
    abha_abdm_sharing: "ఆభా & ఏబీడీఎం షేరింగ్",
    summary_hpi_title: "ప్రస్తుత అనారోగ్య చరిత్ర (HPI)",
    summary_symptoms_title: "నివేదించబడిన లక్షణాలు & హెచ్చరికలు",
    summary_meds_allergies_title: "మందులు & అలెర్జీలు",
    medications_lbl: "మందులు:",
    allergies_lbl: "అలెర్జీలు:",
    source_doc_findings_title: "మూల పత్ర ఫలితాలు",
    review_eyebrow: "సమర్పణకు ముందు తుది ధృవీకరణ",
    review_title: "మీ సందర్శన సమాచారాన్ని సమీక్షించండి",
    review_subtitle: "వైద్యుల క్యూకు సమర్పించే ముందు క్రింది సమాచారం ఖచ్చితమైనదని నిర్ధారించుకోండి.",
    patient_demographics: "👤 రోగి వివరాలు",
    visit_overview: "📋 సందర్శన & సమ్మతి అవలోకనం",
    affirmation_lbl: "ధృవీకరణ:",
    affirmation_note: "సమర్పించు క్లిక్ చేయడం ద్వారా, మీ సమాచారం వైద్యుని కోసం అధికారిక సంప్రదింపు రికార్డుగా తయారు చేయబడుతుంది.",
    back_to_summary: "← సారాంశానికి తిరిగి వెళ్లండి",
    submit_final_visit_btn: "✓ వైద్యుల సమీక్ష కోసం సమర్పించండి",
    success_eyebrow: "సమర్పణ పూర్తయింది",
    success_title: "సమాచారం విజయవంతంగా సమర్పించబడింది",
    success_subtitle: "మీ ఇన్టేక్ రికార్డులు సురక్షితంగా నమోదు చేయబడి క్లినికల్ బృందానికి పంపబడ్డాయి.",
    visit_details_title: "మీ సందర్శన వివరాలు",
    consultation_record_lbl: "సంప్రదింపు రికార్డు:",
    status_lbl: "స్థితి:",
    pending_review_status: "వైద్యుల సమీక్ష పెండింగ్‌లో ఉంది",
    finish_kiosk_btn: "ముగించి కియోస్క్ హోమ్‌కు తిరిగి వెళ్లండి",
    sih_tag: "SIH 2026 రోగి సంరక్షణ",
    portal_btn: "👨‍⚕️ వైద్యుల సమీక్ష",
    call_staff: "🚨 సిబ్బంది సహాయం",

    step_language: "భాష",
    step_identity: "గుర్తింపు",
    step_consent: "సమ్మతి",
    step_intake: "ఆరోగ్య చరిత్ర",
    step_documents: "పత్రాలు & ఓసీఆర్",
    step_review: "సమీక్ష & సమర్పణ",

    welcome_eyebrow: "స్మార్ట్ ఇండియా హ్యాకథాన్ 2026 · ఆరోగ్య సంరక్షణ కియోస్క్",
    welcome_title: "మెడికియోస్క్‌కు స్వాగతం",
    welcome_subtitle: "ఆసుపత్రి ఓపీడీలో వేగవంతమైన, ఖచ్చితమైన మరియు గౌరవప్రదమైన రోగి సంరక్షణ కోసం ఏఐ-సహాయక క్లినికల్ ఇన్టేక్ ప్లాట్‌ఫారమ్.",
    start_touch: "టచ్ / టైప్ ద్వారా ప్రారంభించండి →",
    start_voice: "🎙️ వాయిస్ ద్వారా ప్రారంభించండి",
    privacy_title: "ఖచ్చితమైన రోగి గోప్యత & సమ్మతి రక్షణలు",
    privacy_desc: "సేకరించిన మొత్తం సమాచారం స్థానిక ఆసుపత్రి వ్యవస్థలోనే ఉంటుంది. వైద్యులు సమీక్షించి సంతకం చేసే వరకు ఫలితాలు ఆటోమేటెడ్‌గా ఉంటాయి.",
    kiosk_self_service: "రోగి స్వీయ సేవ",
    self_service_title: "స్వీయ-సేవా కియోస్క్ ఇన్టేక్",
    self_service_desc: "మీ సందర్శనను నమోదు చేయండి, సమ్మతి తెలపండి, వాయిస్ లేదా టచ్ ద్వారా సమాధానమివ్వండి మరియు పత్రాలను స్కాన్ చేయండి.",
    select_lang_begin: "భాషను ఎంచుకోండి & ప్రారంభించండి",
    physician_team: "వైద్యులు & క్లినికల్ బృందం",
    open_physician_workspace: "వైద్యుల వర్క్‌స్పేస్ తెరవండి →",

    lang_eyebrow: "దశ 1 / 6",
    lang_title: "మీ ప్రాధాన్య భాషను ఎంచుకోండి",
    lang_subtitle: "ఈ కియోస్క్ సెషన్‌లో మీరు మాట్లాడటానికి మరియు చదవడానికి ప్రాంతీయ భాషను ఎంచుకోవచ్చు.",
    back_to_welcome: "← స్వాగత స్క్రీన్‌కు వెనుకకు",
    continue_to_identity: "రోగి గుర్తింపునకు కొనసాగించండి →",

    id_eyebrow: "దశ 2 / 6 · రోగి గుర్తింపు",
    id_title: "రోగిని గుర్తించండి లేదా నమోదు చేసుకోండి",
    id_subtitle: "మీ మునుపటి మెడికియోస్క్ పేషెంట్ ఐడీని నమోదు చేయండి, లేదా నేటి సందర్శన కోసం కొత్తగా నమోదు చేసుకోండి.",
    returning_patient: "మునుపటి రోగి",
    have_patient_id: "నాకు పేషెంట్ ఐడీ ఉంది",
    returning_desc: "మీరు గతంలో ఈ కియోస్క్‌లో నమోదు చేసుకున్నట్లయితే, మీ ఐడీని నమోదు చేయండి.",
    patient_id_input_label: "పేషెంట్ ఐడీ సంఖ్య",
    lookup_record_btn: "వివరాలు శోధించండి →",
    new_patient_reg: "కొత్త రోగి నమోదు",
    first_time_title: "ఈ కియోస్క్ వద్ద మొదటిసారి",
    first_time_desc: "సురక్షితమైన సందర్శన కోసం దయచేసి ప్రాథమిక వివరాలను అందించండి.",
    full_name: "పూర్తి పేరు *",
    age: "వయస్సు (సంవత్సరాలు) *",
    gender: "లింగం",
    gender_female: "స్త్రీ",
    gender_male: "పురుషుడు",
    gender_other: "ఇతర",
    gender_unspecified: "చెప్పడానికి ఇష్టపడటం లేదు",
    mobile_number: "మొబైల్ సంఖ్య (ఐచ్ఛికం)",
    abha_number: "ఆభా ఐడీ / ఆయుష్మాన్ భారత్ ఐడీ (ఐచ్ఛికం, 14 అంకెలు)",
    create_patient_btn: "రోగిని సృష్టించి కొనసాగించండి →",
    back_to_language: "← భాషకు వెనుకకు",

    consent_eyebrow: "దశ 3 / 6 · సమాచారంతో కూడిన సమ్మతి",
    consent_title: "వైద్య సమాచార వినియోగానికి సమ్మతి",
    consent_subtitle: "ఆరోగ్య నిబంధనల ప్రకారం, ప్రతి సమ్మతి ప్రయోజనాన్ని స్వతంత్రంగా నియంత్రించవచ్చు. మీరు ఎప్పుడైనా సమ్మతి ఇవ్వవచ్చు లేదా రద్దు చేయవచ్చు.",
    status_active: "క్రియాశీలం (సమ్మతి ఉంది)",
    status_not_granted: "సమ్మతి ఇవ్వబడలేదు",
    status_revoked: "రద్దు చేయబడింది",
    grant_consent_btn: "✓ సమ్మతి ఇవ్వండి",
    revoke_consent_btn: "✕ సమ్మతి రద్దు చేయండి",
    change_patient_btn: "← రోగిని మార్చండి",
    save_start_intake_btn: "సేవ్ చేసి క్లినికల్ ఇన్టేక్ ప్రారంభించండి →",

    purpose_clinical_history_title: "క్లినికల్ హిస్టరీ సేకరణ",
    purpose_clinical_history_desc: "ఈ సందర్శన కోసం మీ లక్షణాలు మరియు వైద్య చరిత్రను సేకరించి భద్రపరచడం.",
    purpose_document_processing_title: "వైద్య పత్రాల ప్రాసెసింగ్",
    purpose_document_processing_desc: "మీరు అప్‌లోడ్ చేసిన పత్రాలపై సురక్షితంగా OCR అమలు చేసి నిల్వ చేయడం.",
    purpose_document_extraction_title: "నిర్మాణాత్మక వైద్య సారం",
    purpose_document_extraction_desc: "ల్యాబ్ పరీక్షలు, మందులు మరియు అలెర్జీల వివరాలను సేకరించడం.",
    purpose_clinical_summary_title: "క్లినికల్ సందర్శన సారాంశం",
    purpose_clinical_summary_desc: "వైద్యుల కోసం అన్ని వాస్తవాలతో సంపూర్ణ సారాంశాన్ని సంకలనం చేయడం.",
    purpose_physician_review_title: "వైద్యుల సమీక్ష అనుమతి",
    purpose_physician_review_desc: "మీ ఇన్టేక్ ప్యాకెట్‌ను పరిశీలించడానికి మీ వైద్య బృందానికి అనుమతి ఇవ్వడం.",
    purpose_abdm_sharing_title: "ఆయుష్మాన్ భారత్ (ABDM) భాగస్వామ్యం",
    purpose_abdm_sharing_desc: "ఆయుష్మాన్ భారత్ డిజిటల్ మిషన్ శాండ్‌బాక్స్ భాగస్వామ్యం. ఐచ్ఛికం.",

    intake_eyebrow: "దశ 4 / 6 · మార్గదర్శక చరిత్ర",
    hello_prefix: "నమస్కారం",
    intake_inst: "ఒకసారి ఒక ప్రశ్నకు మాత్రమే సమాధానం ఇవ్వండి. మీరు మైక్రోఫోన్ ఉపయోగించి మాట్లాడవచ్చు లేదా కింద టైప్ చేయవచ్చు.",
    whisper_pill: "🎙️ గ్రోక్ విస్పర్ ట్రాన్స్‌క్రిప్ట్",
    patient_review_badge: "రోగి సమీక్ష అవసరం",
    whisper_confirm_hint: "గ్రోక్ జీపీటీకి పంపే ముందు దయచేసి మీ మాటలను ధృవీకరించండి లేదా సవరించండి:",
    rerecord_btn: "🔄 మళ్లీ రికార్డ్ చేయండి",
    confirm_send_btn: "✓ ధృవీకరించి ఏఐకి పంపండి →",
    chat_placeholder: "మీ సమాధానాన్ని ఇక్కడ టైప్ చేయండి, లేదా మాట్లాడటానికి 'మైక్' నొక్కండి...",
    speak_mic: "🎙️ మాట్లాడండి (మైక్రోఫోన్)",
    stop_recording: "⏹️ రికార్డింగ్ ఆపండి",
    send_answer: "సమాధానం పంపండి →",
    urgent_banner_title: "దయచేసి వెంటనే సహాయం పొందండి",
    urgent_banner_desc: "ఒక అత్యవసర లక్షణం నమోదైంది. వైద్య నిపుణులు ఆలస్యం లేకుండా పరిశీలించాలి. మెడికియోస్క్ కేవలం సహాయక సాధనం.",
    call_staff_to_kiosk: "కియోస్క్ వద్దకు సిబ్బందిని పిలవండి",
    safety_notice_title: "⚠️ రోగి భద్రతా నోటీసు",
    safety_notice_desc: "తీవ్రమైన ఛాతీ నొప్పి, శ్వాస ఆడకపోవడం లేదా తీవ్ర తలతిరగడం అనిపిస్తే వెంటనే సిబ్బందికి తెలియజేయండి.",
    session_details: "సందర్శన సెషన్ వివరాలు",
    patient_lbl: "రోగి:",
    patient_id_lbl: "రోగి ఐడీ:",
    encounter_id_lbl: "ఎన్‌కౌంటర్ ఐడీ:",
    language_lbl: "భాష:",
    consent_status_lbl: "సమ్మతి స్థితి:",
    back_to_consent: "← సమ్మతికి వెనుకకు",
    proceed_to_docs: "వైద్య పత్రాలకు ముందుకు వెళ్లండి →",

    doc_eyebrow: "దశ 5 / 6 · వైద్య పత్రాలు & ఓసీఆర్",
    doc_title: "నివేదికలు లేదా ప్రిస్క్రిప్షన్‌లను అప్‌లోడ్ చేయండి",
    doc_subtitle: "ల్యాబ్ ఫలితాలు, డిశ్చార్జ్ సారాంశాలు లేదా మునుపటి మందుల చీటీలను అప్‌లోడ్ చేయండి. మద్దతు: PDF, JPG, JPEG, PNG (గరిష్టంగా 10 MB).",
    dropzone_main: "వైద్య పత్రాన్ని ఇక్కడ ఎంచుకోండి లేదా డ్రాప్ చేయండి",
    dropzone_sub: "ఈ పరికరంలో ఫైళ్లను బ్రౌజ్ చేయడానికి క్లిక్ చేయండి",
    run_ocr: "🔍 నెమోట్రాన్ ఓసీఆర్ అమలు చేయండి",
    extract_intel: "సమాచారాన్ని సేకరించండి →",
    back_to_intake: "← ఇన్టేక్‌కు వెనుకకు",
    proceed_to_summary: "క్లినికల్ సారాంశానికి వెళ్లండి →",

    summary_eyebrow: "దశ 6 / 6 · సందర్శన సంకలనం",
    summary_title: "సమగ్ర క్లినికల్ సారాంశం",
    submit_consultation: "వైద్యుల సంప్రదింపు కోసం సమర్పించండి →",
  },

  hi: {
    selected_badge: "चयनित ✓",
    staff_dialog_title: "कर्मचारी सहायता का अनुरोध किया गया",
    staff_dialog_desc: "कृपया कियोस्क पर ही रहें। अस्पताल के कर्मचारी को आपके कियोस्क स्टेशन पर भेजा जा रहा है।",
    staff_dialog_btn: "मैं समझ गया",
    upload_file_btn: "फ़ाइल अभी अपलोड करें",
    uploaded_docs_title: "इस मुलाकात में अपलोड किए गए दस्तावेज़",
    no_docs_uploaded: "अभी तक कोई दस्तावेज़ अपलोड नहीं किया गया है। आप लैब रिपोर्ट अपलोड कर सकते हैं या बिना इसके जारी रख सकते हैं।",
    back_to_docs: "← दस्तावेजों पर वापस जाएं",
    review_submit_visit: "समीक्षा करें और प्रस्तुत करें →",
    abha_abdm_sharing: "आभा और एबीडीएम शेयरिंग",
    summary_hpi_title: "वर्तमान बीमारी का इतिहास (HPI)",
    summary_symptoms_title: "दर्ज किए गए लक्षण और रेड फ्लैग्स",
    summary_meds_allergies_title: "दवाएं और एलर्जी",
    medications_lbl: "दवाएं:",
    allergies_lbl: "एलर्जी:",
    source_doc_findings_title: "मूल दस्तावेज़ निष्कर्ष",
    review_eyebrow: "प्रस्तुत करने से पहले अंतिम सत्यापन",
    review_title: "अपनी मुलाकात की जानकारी की समीक्षा करें",
    review_subtitle: "चिकित्सक कतार में जमा करने से पहले सुनिश्चित करें कि नीचे दी गई जानकारी सही है।",
    patient_demographics: "👤 मरीज का विवरण",
    visit_overview: "📋 मुलाकात और सहमति विवरण",
    affirmation_lbl: "पुष्टिकरण:",
    affirmation_note: "सबमिट पर क्लिक करने से, आपकी जानकारी उपस्थित चिकित्सक के लिए एक आधिकारिक परामर्श रिकॉर्ड के रूप में तैयार की जाएगी।",
    back_to_summary: "← सारांश पर वापस जाएं",
    submit_final_visit_btn: "✓ चिकित्सक समीक्षा के लिए प्रस्तुत करें",
    success_eyebrow: "प्रस्तुत करना पूर्ण हुआ",
    success_title: "जानकारी सफलतापूर्वक प्रस्तुत की गई",
    success_subtitle: "आपका इनटेक रिकॉर्ड सुरक्षित रूप से दर्ज कर दिया गया है और क्लिनिकल टीम को भेज दिया गया है।",
    visit_details_title: "आपकी मुलाकात का विवरण",
    consultation_record_lbl: "परामर्श रिकॉर्ड:",
    status_lbl: "स्थिति:",
    pending_review_status: "चिकित्सक समीक्षा लंबित",
    finish_kiosk_btn: "समाप्त करें और कियोस्क होम पर लौटें",
    sih_tag: "SIH 2026 रोगी देखभाल",
    portal_btn: "👨‍⚕️ चिकित्सक समीक्षा",
    call_staff: "🚨 कर्मचारी सहायता",

    step_language: "भाषा",
    step_identity: "पहचान",
    step_consent: "सहमति",
    step_intake: "स्वास्थ्य इतिहास",
    step_documents: "दस्तावेज़ और ओसीआर",
    step_review: "समीक्षा और जमा करें",

    welcome_eyebrow: "स्मार्ट इंडिया हैकाथॉन 2026 · स्वास्थ्य सेवा कियोस्क",
    welcome_title: "मेडीकियोस्क में आपका स्वागत है",
    welcome_subtitle: "अस्पताल ओपीडी में त्वरित, सटीक और सम्मानजनक रोगी देखभाल के लिए एआई-सहायता प्राप्त क्लिनिकल इनटेक प्लेटफ़ॉर्म।",
    start_touch: "स्क्रीन छूकर / लिखकर शुरू करें →",
    start_voice: "🎙️ बोलकर शुरू करें (माइक्रोफ़ोन)",
    privacy_title: "सख्त रोगी गोपनीयता और सहमति सुरक्षा",
    privacy_desc: "एकत्र की गई सभी जानकारी स्थानीय अस्पताल प्रणाली के भीतर रहती है। चिकित्सक द्वारा समीक्षा और हस्ताक्षर किए जाने तक परिणाम स्वचालित होते हैं।",
    kiosk_self_service: "रोगी स्वयं सेवा",
    self_service_title: "स्वयं-सेवा कियोस्क इनटेक",
    self_service_desc: "पंजीकरण करें, सहमति दें, बोलकर या लिखकर उत्तर दें और अपनी मेडिकल रिपोर्ट स्कैन करें।",
    select_lang_begin: "भाषा चुनें और शुरू करें",
    physician_team: "चिकित्सक और क्लिनिकल टीम",
    open_physician_workspace: "चिकित्सक कार्यक्षेत्र खोलें →",

    lang_eyebrow: "चरण 1 / 6",
    lang_title: "अपनी पसंदीदा भाषा चुनें",
    lang_subtitle: "इस कियोस्क सत्र के दौरान आप अपनी पसंदीदा भाषा में बोल और पढ़ सकते हैं।",
    back_to_welcome: "← स्वागत स्क्रीन पर वापस",
    continue_to_identity: "रोगी पहचान पर आगे बढ़ें →",

    id_eyebrow: "चरण 2 / 6 · रोगी पहचान",
    id_title: "रोगी की पहचान करें या पंजीकरण करें",
    id_subtitle: "अपनी मौजूदा मेडीकियोस्क रोगी आईडी दर्ज करें, या आज के परामर्श के लिए नया पंजीकरण करें।",
    returning_patient: "पुराने रोगी",
    have_patient_id: "मेरे पास रोगी आईडी है",
    returning_desc: "यदि आपने पहले इस कियोस्क पर पंजीकरण कराया है, तो अपनी आईडी दर्ज करें।",
    patient_id_input_label: "रोगी आईडी संख्या",
    lookup_record_btn: "विवरण खोजें →",
    new_patient_reg: "नया रोगी पंजीकरण",
    first_time_title: "इस कियोस्क पर पहली बार",
    first_time_desc: "सुरक्षित परामर्श के लिए कृपया बुनियादी विवरण प्रदान करें।",
    full_name: "पूरा नाम *",
    age: "आयु (वर्ष) *",
    gender: "लिंग",
    gender_female: "महिला",
    gender_male: "पुरुष",
    gender_other: "अन्य",
    gender_unspecified: "नहीं बताना चाहते",
    mobile_number: "मोबाइल नंबर (वैकल्पिक)",
    abha_number: "आभा आईडी / आयुष्मान भारत आईडी (वैकल्पिक, 14 अंक)",
    create_patient_btn: "रोगी बनाएं और आगे बढ़ें →",
    back_to_language: "← भाषा पर वापस",

    consent_eyebrow: "चरण 3 / 6 · सूचित सहमति",
    consent_title: "चिकित्सा जानकारी के उपयोग की सहमति",
    consent_subtitle: "स्वास्थ्य नियमों के तहत, आप प्रत्येक उद्देश्य को स्वतंत्र रूप से नियंत्रित करते हैं। आप किसी भी समय सहमति दे या रद्द कर सकते हैं।",
    status_active: "सक्रिय (सहमति प्राप्त)",
    status_not_granted: "सहमति नहीं दी गई",
    status_revoked: "रद्द की गई",
    grant_consent_btn: "✓ सहमति दें",
    revoke_consent_btn: "✕ सहमति रद्द करें",
    change_patient_btn: "← रोगी बदलें",
    save_start_intake_btn: "सहेजें और इनटेक शुरू करें →",

    purpose_clinical_history_title: "क्लिनिकल इतिहास संग्रह",
    purpose_clinical_history_desc: "इस परामर्श के लिए आपके लक्षणों और चिकित्सा इतिहास को सुरक्षित रूप से एकत्र करना।",
    purpose_document_processing_title: "चिकित्सा दस्तावेज़ प्रसंस्करण",
    purpose_document_processing_desc: "अपलोड की गई फ़ाइलों पर ओसीआर (OCR) चलाना और उन्हें सुरक्षित रखना।",
    purpose_document_extraction_title: "संरचित चिकित्सा निष्कर्षण",
    purpose_document_extraction_desc: "लैब रिपोर्ट, दवाओं और एलर्जी की जानकारी को निकालना।",
    purpose_clinical_summary_title: "क्लिनिकल परामर्श सारांश",
    purpose_clinical_summary_desc: "डॉक्टर के लिए सभी तथ्यों का एक संपूर्ण सारांश तैयार करना।",
    purpose_physician_review_title: "चिकित्सक समीक्षा अनुमति",
    purpose_physician_review_desc: "आपकी चिकित्सा टीम को आपके इनटेक पैकेट की समीक्षा करने की अनुमति देना।",
    purpose_abdm_sharing_title: "आयुष्मान भारत (ABDM) साझाकरण",
    purpose_abdm_sharing_desc: "आयुष्मान भारत डिजिटल मिशन सैंडबॉक्स साझाकरण। वैकल्पिक।",

    intake_eyebrow: "चरण 4 / 6 · निर्देशित इतिहास",
    hello_prefix: "नमस्ते",
    intake_inst: "एक समय में केवल एक प्रश्न का उत्तर दें। आप माइक्रोफ़ोन से बोल सकते हैं या नीचे लिख सकते हैं।",
    whisper_pill: "🎙️ ग्रॉक व्हिस्पर प्रतिलेख",
    patient_review_badge: "रोगी समीक्षा आवश्यक",
    whisper_confirm_hint: "ग्रॉक जीपीटी को भेजने से पहले कृपया अपने शब्दों की जांच करें:",
    rerecord_btn: "🔄 फिर से बोलें",
    confirm_send_btn: "✓ पुष्टि करें और एआई को भेजें →",
    chat_placeholder: "अपना उत्तर यहाँ लिखें, या बोलने के लिए 'माइक' दबाएं...",
    speak_mic: "🎙️ बोलें (माइक्रोफ़ोन)",
    stop_recording: "⏹️ रिकॉर्डिंग रोकें",
    send_answer: "उत्तर भेजें →",
    urgent_banner_title: "कृपया तुरंत सहायता प्राप्त करें",
    urgent_banner_desc: "एक गंभीर लक्षण की सूचना मिली है। डॉक्टर को बिना देरी के आपकी जांच करनी चाहिए।",
    call_staff_to_kiosk: "कर्मचारी को कियोस्क पर बुलाएं",
    safety_notice_title: "⚠️ रोगी सुरक्षा सूचना",
    safety_notice_desc: "सीने में तेज दर्द, सांस लेने में तकलीफ या चक्कर आने पर तुरंत कर्मचारी सहायता लें।",
    session_details: "परामर्श सत्र विवरण",
    patient_lbl: "रोगी:",
    patient_id_lbl: "रोगी आईडी:",
    encounter_id_lbl: "सत्र आईडी:",
    language_lbl: "भाषा:",
    consent_status_lbl: "सहमति स्थिति:",
    back_to_consent: "← सहमति पर वापस",
    proceed_to_docs: "चिकित्सा दस्तावेज़ों पर जाएं →",

    doc_eyebrow: "चरण 5 / 6 · चिकित्सा दस्तावेज़ और ओसीआर",
    doc_title: "रिपोर्ट या पर्ची अपलोड करें",
    doc_subtitle: "लैब टेस्ट रिपोर्ट या पिछले नुस्खे अपलोड करें। समर्थित: PDF, JPG, JPEG, PNG (अधिकतम 10 MB)।",
    dropzone_main: "दस्तावेज़ यहाँ चुनें या छोड़ें",
    dropzone_sub: "इस डिवाइस से फ़ाइल चुनने के लिए क्लिक करें",
    run_ocr: "🔍 नेमोट्रॉन ओसीआर चलाएं",
    extract_intel: "जानकारी निकालें →",
    back_to_intake: "← इनटेक पर वापस",
    proceed_to_summary: "क्लिनिकल सारांश पर जाएं →",

    summary_eyebrow: "चरण 6 / 6 · सारांश और सबमिशन",
    summary_title: "व्यापक क्लिनिकल सारांश",
    submit_consultation: "डॉक्टर परामर्श के लिए जमा करें →",
  },

  ta: {
    selected_badge: "தேர்ந்தெடுக்கப்பட்டது ✓",
    staff_dialog_title: "பணியாளர் உதவி கோரப்பட்டது",
    staff_dialog_desc: "தயவுசெய்து கியோஸ்க்கில் இருங்கள். மருத்துவமனை பணியாளர் உங்கள் இடத்திற்கு அழைக்கப்படுகிறார்.",
    staff_dialog_btn: "எனக்கு புரிகிறது",
    upload_file_btn: "கோப்பை இப்போது பதிவேற்றவும்",
    uploaded_docs_title: "இந்த வருகையில் பதிவேற்றப்பட்ட ஆவணங்கள்",
    no_docs_uploaded: "இதுவரை எந்த ஆவணமும் பதிவேற்றப்படவில்லை. நீங்கள் ஆய்வக அறிக்கையை பதிவேற்றலாம் அல்லது இல்லாமலும் தொடரலாம்.",
    back_to_docs: "← ஆவணங்களுக்கு திரும்பு",
    review_submit_visit: "மதிப்பாய்வு செய்து சமர்ப்பிக்கவும் →",
    abha_abdm_sharing: "ஆபா & ஏபிடிஎம் பகிர்வு",
    summary_hpi_title: "தற்போதைய நோய் வரலாறு (HPI)",
    summary_symptoms_title: "பதிவான அறிகுறிகள் மற்றும் எச்சரிக்கைகள்",
    summary_meds_allergies_title: "மருந்துகள் மற்றும் ஒவ்வாமைகள்",
    medications_lbl: "மருந்துகள்:",
    allergies_lbl: "ஒவ்வாமைகள்:",
    source_doc_findings_title: "மூல ஆவண முடிவுகள்",
    review_eyebrow: "சமர்ப்பிப்பதற்கு முன் இறுதி சரிபார்ப்பு",
    review_title: "உங்கள் வருகை தகவலை மதிப்பாய்வு செய்யவும்",
    review_subtitle: "மருத்துவர் வரிசையில் சமர்ப்பிக்கும் முன் கீழே உள்ள தகவல்கள் துல்லியமானவை என்பதை உறுதிப்படுத்தவும்.",
    patient_demographics: "👤 நோயாளி விவரங்கள்",
    visit_overview: "📋 வருகை மற்றும் சம்மத கண்ணோட்டம்",
    affirmation_lbl: "உறுதிப்படுத்தல்:",
    affirmation_note: "சமர்ப்பி என்பதைக் கிளிக் செய்வதன் மூலம், உங்கள் தகவல் மருத்துவருக்கான அதிகாரப்பூர்வ ஆலோசனைக் பதிவாக தயாரிக்கப்படும்.",
    back_to_summary: "← சுருக்கத்திற்கு திரும்பு",
    submit_final_visit_btn: "✓ மருத்துவர் மதிப்பாய்வுக்கு சமர்ப்பிக்கவும்",
    success_eyebrow: "சமர்ப்பித்தல் முடிந்தது",
    success_title: "தகவல் வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது",
    success_subtitle: "உங்கள் பதிவுகள் பாதுகாப்பாக பதிவு செய்யப்பட்டு மருத்துவக் குழுவிற்கு மாற்றப்பட்டுள்ளன.",
    visit_details_title: "உங்கள் வருகை விவரங்கள்",
    consultation_record_lbl: "ஆலோசனை பதிவு:",
    status_lbl: "நிலை:",
    pending_review_status: "மருத்துவர் ஆய்வு நிலுவையில் உள்ளது",
    finish_kiosk_btn: "முடித்து கியோஸ்க் முகப்புக்குத் திரும்பு",
    sih_tag: "SIH 2026 நோயாளி பராமரிப்பு",
    portal_btn: "👨‍⚕️ மருத்துவர் மதிப்பாய்வு",
    call_staff: "🚨 பணியாளர் உதவி",

    step_language: "மொழி",
    step_identity: "அடையாளம்",
    step_consent: "சம்மதம்",
    step_intake: "மருத்துவ வரலாறு",
    step_documents: "ஆவணங்கள் & OCR",
    step_review: "மதிப்பாய்வு & சமர்ப்பி",

    welcome_eyebrow: "ஸ்மார்ட் இந்தியா ஹேக்கத்தான் 2026 · சுகாதார கியோஸ்க்",
    welcome_title: "மெடிகியோஸ்க்கிற்கு வரவேற்கிறோம்",
    welcome_subtitle: "மருத்துவமனை ஓபிடியில் விரைவான, துல்லியமான நோயாளி பராமரிப்புக்கான AI-உதவி உட்கொள்ளும் தளம்.",
    start_touch: "திரையைத் தொட்டு தொடங்கவும் →",
    start_voice: "🎙️ குரல் மூலம் தொடங்கவும்",
    privacy_title: "நோயாளி தனியுரிமை & சம்மத பாதுகாப்பு",
    privacy_desc: "சேகரிக்கப்பட்ட அனைத்து தகவல்களும் மருத்துவமனை அமைப்பிற்குள்ளேயே இருக்கும். மருத்துவர் சரிபார்க்கும் வரை முடிவுகள் தானியங்கி ஆகும்.",
    kiosk_self_service: "நோயாளி சுய சேவை",
    self_service_title: "சுய-சேவை கியோஸ்க் இன்டேக்",
    self_service_desc: "பதிவு செய்யுங்கள், சம்மதம் அளியுங்கள், குரல் அல்லது தொடுதல் மூலம் பதிலளியுங்கள் மற்றும் ஆவணங்களை ஸ்கேன் செய்யுங்கள்.",
    select_lang_begin: "மொழியைத் தேர்ந்தெடுத்து தொடங்கவும்",
    physician_team: "மருத்துவர் மற்றும் கிளினிக்கல் குழு",
    open_physician_workspace: "மருத்துவர் பணியிடத்தைத் திறக்கவும் →",

    lang_eyebrow: "படி 1 / 6",
    lang_title: "உங்கள் விருப்ப மொழியைத் தேர்ந்தெடுக்கவும்",
    lang_subtitle: "இந்த கியோஸ்க் அமர்வில் நீங்கள் பேசவும் படிக்கவும் வசதியான மொழியைத் தேர்வுசெய்யலாம்.",
    back_to_welcome: "← வரவேற்பு திரைக்கு திரும்பு",
    continue_to_identity: "நோயாளி அடையாளத்திற்கு செல்லவும் →",

    id_eyebrow: "படி 2 / 6 · நோயாளி அடையாளம்",
    id_title: "நோயாளியை அடையாளம் காணவும் அல்லது பதிவு செய்யவும்",
    id_subtitle: "உங்கள் முந்தைய நோயாளி ஐடியை உள்ளிடவும், அல்லது புதிய பதிவைச் செய்யவும்.",
    returning_patient: "முந்தைய நோயாளி",
    have_patient_id: "என்னிடம் நோயாளி ஐடி உள்ளது",
    returning_desc: "நீங்கள் முன்பு பதிவு செய்திருந்தால், உங்கள் ஐடியை உள்ளிடவும்.",
    patient_id_input_label: "நோயாளி ஐடி எண்",
    lookup_record_btn: "விவரங்களைத் தேடுங்கள் →",
    new_patient_reg: "புதிய நோயாளி பதிவு",
    first_time_title: "இந்த கியோஸ்க்கில் முதல் முறை",
    first_time_desc: "பாதுகாப்பான சந்திப்பிற்கு அடிப்படை விவரங்களை உள்ளிடவும்.",
    full_name: "முழு பெயர் *",
    age: "வயது (ஆண்டுகள்) *",
    gender: "பாலினம்",
    gender_female: "பெண்",
    gender_male: "ஆண்",
    gender_other: "மற்றவை",
    gender_unspecified: "கூற விரும்பவில்லை",
    mobile_number: "மொபைல் எண் (விருப்பத்தேர்வு)",
    abha_number: "ஆபா ஐடி / ஆயுஷ்மான் பாரத் ஐடி (விருப்பத்தேர்வு, 14 இலக்கங்கள்)",
    create_patient_btn: "பதிவு செய்து தொடரவும் →",
    back_to_language: "← மொழிக்கு திரும்பு",

    consent_eyebrow: "படி 3 / 6 · நோயாளி சம்மதம்",
    consent_title: "மருத்துவ தகவல் பயன்பாட்டிற்கான சம்மதம்",
    consent_subtitle: "ஒவ்வொரு நோக்கத்தையும் நீங்கள் கட்டுப்படுத்துகிறீர்கள். நீங்கள் எப்போது வேண்டுமானாலும் சம்மதத்தை அளிக்கலாம் அல்லது திரும்பப் பெறலாம்.",
    status_active: "செயலில் உள்ளது (சம்மதிக்கப்பட்டது)",
    status_not_granted: "சம்மதம் அளிக்கப்படவில்லை",
    status_revoked: "திரும்பப் பெறப்பட்டது",
    grant_consent_btn: "✓ சம்மதம் அளிக்கவும்",
    revoke_consent_btn: "✕ சம்மதத்தை திரும்பப் பெறவும்",
    change_patient_btn: "← நோயாளியை மாற்றவும்",
    save_start_intake_btn: "சேமித்து இன்டேக்கை தொடங்கவும் →",

    purpose_clinical_history_title: "மருத்துவ வரலாறு சேகரிப்பு",
    purpose_clinical_history_desc: "உங்கள் அறிகுறிகள் மற்றும் மருத்துவ வரலாற்றை சேகரித்து கட்டமைப்பது.",
    purpose_document_processing_title: "மருத்துவ ஆவண செயலாக்கம்",
    purpose_document_processing_desc: "பதிவேற்றப்பட்ட ஆவணங்களில் OCR செய்து பாதுகாப்பாக சேமிப்பது.",
    purpose_document_extraction_title: "கட்டமைக்கப்பட்ட மருத்துவ பிரித்தெடுத்தல்",
    purpose_document_extraction_desc: "ஆய்வக அறிக்கைகள், மருந்துகள் மற்றும் ஒவ்வாமைகளை பிரித்தெடுப்பது.",
    purpose_clinical_summary_title: "மருத்துவ வருகை சுருக்கம்",
    purpose_clinical_summary_desc: "மருத்துவருக்கான முழுமையான சுருக்கத்தை தொகுப்பது.",
    purpose_physician_review_title: "மருத்துவர் மதிப்பாய்வு அனுமதி",
    purpose_physician_review_desc: "மருத்துவர் உங்கள் தகவல்களை மதிப்பாய்வு செய்ய அனுமதிப்பது.",
    purpose_abdm_sharing_title: "ஆயுஷ்மான் பாரத் (ABDM) பகிர்வு",
    purpose_abdm_sharing_desc: "ஆயுஷ்மான் பாரத் டிஜிட்டல் மிஷன் பகிர்வு. விருப்பத்தேர்வு.",

    intake_eyebrow: "படி 4 / 6 · வழிகாட்டப்பட்ட வரலாறு",
    hello_prefix: "வணக்கம்",
    intake_inst: "ஒரு நேரத்தில் ஒரு கேள்விக்கு மட்டுமே பதிலளிக்கவும். நீங்கள் மைக்ரோஃபோன் மூலம் பேசலாம் அல்லது கீழே தட்டச்சு செய்யலாம்.",
    whisper_pill: "🎙️ க்ரோக் விஸ்பர் டிரான்ஸ்கிரிப்ட்",
    patient_review_badge: "நோயாளி சரிபார்ப்பு தேவை",
    whisper_confirm_hint: "AI க்கு அனுப்பும் முன் உங்கள் வார்த்தைகளை சரிபார்க்கவும்:",
    rerecord_btn: "🔄 மீண்டும் பதிவு செய்யவும்",
    confirm_send_btn: "✓ உறுதிசெய்து AIக்கு அனுப்பவும் →",
    chat_placeholder: "உங்கள் பதிலை இங்கே தட்டச்சு செய்யவும், அல்லது பேச 'மைக்' அழுத்தவும்...",
    speak_mic: "🎙️ பேசுங்கள் (மைக்ரோஃபோன்)",
    stop_recording: "⏹️ பதிவை நிறுத்துங்கள்",
    send_answer: "பதிலை அனுப்பு →",
    urgent_banner_title: "தயவுசெய்து உடனடியாக உதவி பெறவும்",
    urgent_banner_desc: "அவசர அறிகுறி பதிவாகியுள்ளது. மருத்துவர் உடனடியாக பரிசோதிக்க வேண்டும்.",
    call_staff_to_kiosk: "பணியாளரை அழைக்கவும்",
    safety_notice_title: "⚠️ நோயாளி பாதுகாப்பு அறிவிப்பு",
    safety_notice_desc: "நெஞ்சு வலி, மூச்சுத் திணறல் அல்லது தலைசுற்றல் ஏற்பட்டால் உடனே பணியாளர் உதவி பெறவும்.",
    session_details: "அமர்வு விவரங்கள்",
    patient_lbl: "நோயாளி:",
    patient_id_lbl: "நோயாளி ஐடி:",
    encounter_id_lbl: "அமர்வு ஐடி:",
    language_lbl: "மொழி:",
    consent_status_lbl: "சம்மத நிலை:",
    back_to_consent: "← சம்மதத்திற்கு திரும்பு",
    proceed_to_docs: "மருத்துவ ஆவணங்களுக்குச் செல்லவும் →",

    doc_eyebrow: "படி 5 / 6 · ஆவணங்கள் & OCR",
    doc_title: "அறிக்கைகள் அல்லது மருந்துச் சீட்டுகளைப் பதிவேற்றவும்",
    doc_subtitle: "ஆய்வக அறிக்கைகள் அல்லது மருந்துச் சீட்டுகளைப் பதிவேற்றவும். ஆதரிக்கப்படுபவை: PDF, JPG, JPEG, PNG (அதிகபட்சம் 10 MB).",
    dropzone_main: "ஆவணத்தை இங்கே தேர்ந்தெடுக்கவும்",
    dropzone_sub: "கோப்புகளைத் தேர்ந்தெடுக்க கிளிக் செய்யவும்",
    run_ocr: "🔍 நெமோட்ரான் OCR இயக்கவும்",
    extract_intel: "தகவலைப் பிரித்தெடுக்கவும் →",
    back_to_intake: "← இன்டேக்கிற்கு திரும்பு",
    proceed_to_summary: "சுருக்கத்திற்குச் செல்லவும் →",

    summary_eyebrow: "படி 6 / 6 · சுருக்கம் & சமர்ப்பிப்பு",
    summary_title: "விரிவான மருத்துவ சுருக்கம்",
    submit_consultation: "மருத்துவர் ஆலோசனைக்கு சமர்ப்பிக்கவும் →",
  },

  bn: {
    selected_badge: "নির্বাচিত ✓",
    staff_dialog_title: "কর্মী সহায়তা অনুরোধ করা হয়েছে",
    staff_dialog_desc: "অনুগ্রহ করে কিয়স্কে অপেক্ষা করুন। একজন কর্মী আপনার কিয়স্ক স্টেশনে আসছেন।",
    staff_dialog_btn: "আমি বুঝেছি",
    upload_file_btn: "ফাইল এখনই আপলোড করুন",
    uploaded_docs_title: "এই সাক্ষাতে আপলোড করা নথি",
    no_docs_uploaded: "এখনও কোনো নথি আপলোড করা হয়নি। আপনি ল্যাব রিপোর্ট আপলোড করতে পারেন বা ছাড়াই এগিয়ে যেতে পারেন।",
    back_to_docs: "← নথিতে ফিরে যান",
    review_submit_visit: "পর্যালোচনা করুন ও জমা দিন →",
    abha_abdm_sharing: "আভা ও এবিডিএম ভাগাভাগি",
    summary_hpi_title: "বর্তমান অসুস্থতার ইতিহাস (HPI)",
    summary_symptoms_title: "প্রতিবেদিত লক্ষণ ও সতর্কতা",
    summary_meds_allergies_title: "ওষুধ ও অ্যালার্জি",
    medications_lbl: "ওষুধসমূহ:",
    allergies_lbl: "অ্যালার্জি:",
    source_doc_findings_title: "উৎস নথির ফলাফল",
    review_eyebrow: "জমা দেওয়ার আগে চূড়ান্ত যাচাইকরণ",
    review_title: "আপনার সাক্ষাতের তথ্য পর্যালোচনা করুন",
    review_subtitle: "চিকিৎসক সারিতে জমা দেওয়ার আগে নিচের তথ্য সঠিক কিনা তা নিশ্চিত করুন।",
    patient_demographics: "👤 রোগীর বিবরণ",
    visit_overview: "📋 সাক্ষাৎ ও সম্মতির বিবরণ",
    affirmation_lbl: "নিশ্চিতকরণ:",
    affirmation_note: "জমা দিন ক্লিক করার মাধ্যমে, আপনার তথ্য চিকিৎসকের জন্য একটি অফিসিয়াল রেকর্ড হিসেবে প্রস্তুত হবে।",
    back_to_summary: "← সারসংক্ষেপে ফিরে যান",
    submit_final_visit_btn: "✓ চিকিৎসক পর্যালোচনার জন্য জমা দিন",
    success_eyebrow: "জমা দেওয়া সম্পন্ন হয়েছে",
    success_title: "তথ্য সফলভাবে জমা দেওয়া হয়েছে",
    success_subtitle: "আপনার রেকর্ড নিরাপদে নথিভুক্ত করা হয়েছে এবং ওপিডি ক্লিনিকাল টিমের কাছে পাঠানো হয়েছে।",
    visit_details_title: "আপনার সাক্ষাতের বিবরণ",
    consultation_record_lbl: "পরামর্শ রেকর্ড:",
    status_lbl: "অবস্থা:",
    pending_review_status: "চিকিৎসক পর্যালোচনা মুলতুবি",
    finish_kiosk_btn: "সমাপ্ত করে কিয়স্ক হোমে ফিরে যান",
    sih_tag: "SIH 2026 রোগী যত্ন",
    portal_btn: "👨‍⚕️ চিকিৎসক পর্যালোচনা",
    call_staff: "🚨 কর্মী সহায়তা",

    step_language: "ভাষা",
    step_identity: "পরিচয়",
    step_consent: "সম্মতি",
    step_intake: "স্বাস্থ্য ইতিহাস",
    step_documents: "নথি ও OCR",
    step_review: "পর্যালোচনা ও জমা",

    welcome_eyebrow: "স্মার্ট ইন্ডিয়া হ্যাকাথন ২০২৬ · স্বাস্থ্যসেবা কিয়স্ক",
    welcome_title: "মেডিকিয়স্কে স্বাগতম",
    welcome_subtitle: "হাসপাতাল ওপিডিতে দ্রুত, নির্ভুল এবং মর্যাদাপূর্ণ রোগী যত্নের জন্য এআই-সহায়তাপ্রাপ্ত ক্লিনিকাল ইনটেক প্ল্যাটফর্ম।",
    start_touch: "স্ক্রিন স্পর্শ করে শুরু করুন →",
    start_voice: "🎙️ কণ্ঠস্বর দিয়ে শুরু করুন",
    privacy_title: "কঠোর রোগী গোপনীয়তা ও সম্মতি সুরক্ষা",
    privacy_desc: "সংগৃহীত সমস্ত তথ্য স্থানীয় হাসপাতাল সিস্টেমের মধ্যেই থাকে। চিকিৎসক স্বাক্ষর না করা পর্যন্ত ফলাফল স্বয়ংক্রিয় থাকে।",
    kiosk_self_service: "রোগী স্বয়ং সেবা",
    self_service_title: "স্বয়ং-সেবা কিয়স্ক ইনটেক",
    self_service_desc: "নিবন্ধন করুন, সম্মতি দিন, কথা বলে বা লিখে উত্তর দিন এবং রিপোর্ট স্ক্যান করুন।",
    select_lang_begin: "ভাষা নির্বাচন করুন ও শুরু করুন",
    physician_team: "চিকিৎসক ও ক্লিনিকাল টিম",
    open_physician_workspace: "চিকিৎসক ওয়ার্কস্পেস খুলুন →",

    lang_eyebrow: "ধাপ ১ / ৬",
    lang_title: "আপনার পছন্দের ভাষা নির্বাচন করুন",
    lang_subtitle: "এই কিয়স্ক সেশনে আপনি কথা বলতে এবং পড়তে আঞ্চলিক ভাষা বেছে নিতে পারেন।",
    back_to_welcome: "← স্বাগত স্ক্রিনে ফিরে যান",
    continue_to_identity: "রোগীর পরিচয়ে এগিয়ে যান →",

    id_eyebrow: "ধাপ ২ / ৬ · রোগীর পরিচয়",
    id_title: "রোগীর পরিচয় দিন বা নিবন্ধন করুন",
    id_subtitle: "আপনার পূর্ববর্তী পেশেন্ট আইডি লিখুন, অথবা আজকের জন্য নতুন নিবন্ধন করুন।",
    returning_patient: "পূর্ববর্তী রোগী",
    have_patient_id: "আমার একটি পেশেন্ট আইডি আছে",
    returning_desc: "আপনি যদি আগে নিবন্ধিত হয়ে থাকেন, তবে আপনার আইডি লিখুন।",
    patient_id_input_label: "পেশেন্ট আইডি নম্বর",
    lookup_record_btn: "বিবরণ খুঁজুন →",
    new_patient_reg: "নতুন রোগী নিবন্ধন",
    first_time_title: "এই কিয়স্কে প্রথমবার",
    first_time_desc: "নিরাপদ সাক্ষাতের জন্য অনুগ্রহ করে প্রাথমিক বিবরণ প্রদান করুন।",
    full_name: "সম্পূর্ণ নাম *",
    age: "বয়স (বছর) *",
    gender: "লিঙ্গ",
    gender_female: "মহিলা",
    gender_male: "পুরুষ",
    gender_other: "অন্যান্য",
    gender_unspecified: "বলতে অনিচ্ছুক",
    mobile_number: "মোবাইল নম্বর (ঐচ্ছিক)",
    abha_number: "আভা আইডি / আয়ুষ্মান ভারত আইডি (ঐচ্ছিক, ১৪ সংখ্যা)",
    create_patient_btn: "রোগী তৈরি করে এগিয়ে যান →",
    back_to_language: "← ভাষায় ফিরে যান",

    consent_eyebrow: "ধাপ ৩ / ৬ · অবহিত সম্মতি",
    consent_title: "চিকিৎসা তথ্য ব্যবহারের সম্মতি",
    consent_subtitle: "স্বাস্থ্য নীতি অনুযায়ী, আপনি প্রতিটি উদ্দেশ্য স্বাধীনভাবে নিয়ন্ত্রণ করেন। আপনি যেকোনো সময় সম্মতি দিতে বা প্রত্যাহার করতে পারেন।",
    status_active: "সক্রিয় (সম্মতি প্রাপ্ত)",
    status_not_granted: "সম্মতি দেওয়া হয়নি",
    status_revoked: "প্রত্যাহার করা হয়েছে",
    grant_consent_btn: "✓ সম্মতি দিন",
    revoke_consent_btn: "✕ সম্মতি প্রত্যাহার করুন",
    change_patient_btn: "← রোগী পরিবর্তন করুন",
    save_start_intake_btn: "সংরক্ষণ করুন ও ইনটেক শুরু করুন →",

    purpose_clinical_history_title: "ক্লিনিকাল ইতিহাস সংগ্রহ",
    purpose_clinical_history_desc: "এই সাক্ষাতের জন্য আপনার লক্ষণ ও চিকিৎসার ইতিহাস সংগ্রহ করা।",
    purpose_document_processing_title: "চিকিৎসা নথি প্রক্রিয়াকরণ",
    purpose_document_processing_desc: "আপলোড করা ফাইলে OCR পরিচালনা করা এবং নিরাপদে সংরক্ষণ করা।",
    purpose_document_extraction_title: "গঠনমূলক চিকিৎসা নিষ্কাশন",
    purpose_document_extraction_desc: "ল্যাব ফলাফল, ওষুধ এবং অ্যালার্জির তথ্য বের করা।",
    purpose_clinical_summary_title: "ক্লিনিকাল ভিজিট সারাংশ",
    purpose_clinical_summary_desc: "চিকিৎসকের জন্য সম্পূর্ণ সারাংশ প্রস্তুত করা।",
    purpose_physician_review_title: "চিকিৎসক পর্যালোচনা অনুমতি",
    purpose_physician_review_desc: "চিকিৎসককে আপনার ইনটেক প্যাকেট পর্যালোচনা করার অনুমতি দেওয়া।",
    purpose_abdm_sharing_title: "আয়ুষ্মান ভারত (ABDM) ভাগাভাগি",
    purpose_abdm_sharing_desc: "আয়ুষ্মান ভারত ডিজিটাল মিশন স্যান্ডবক্স ভাগাভাগি। ঐচ্ছিক।",

    intake_eyebrow: "ধাপ ৪ / ৬ · নির্দেশিত ইতিহাস",
    hello_prefix: "নমস্কার",
    intake_inst: "একবারে একটি প্রশ্নের উত্তর দিন। আপনি মাইক্রোফোন দিয়ে কথা বলতে পারেন বা নিচে লিখতে পারেন।",
    whisper_pill: "🎙️ গ্রক হুইস্পার প্রতিলিপি",
    patient_review_badge: "রোগীর পর্যালোচনা প্রয়োজন",
    whisper_confirm_hint: "এআই-তে পাঠানোর আগে অনুগ্রহ করে যাচাই বা সম্পাদনা করুন:",
    rerecord_btn: "🔄 পুনরায় রেকর্ড করুন",
    confirm_send_btn: "✓ নিশ্চিত করুন এবং এআই-তে পাঠান →",
    chat_placeholder: "আপনার উত্তর এখানে লিখুন, অথবা কথা বলতে 'মাইক' চাপুন...",
    speak_mic: "🎙️ বলুন (মাইক্রোফোন)",
    stop_recording: "⏹️ রেকর্ডিং বন্ধ করুন",
    send_answer: "উত্তর পাঠান →",
    urgent_banner_title: "অনুগ্রহ করে অবিলম্বে সহায়তা নিন",
    urgent_banner_desc: "একটি গুরুতর উপসর্গের তথ্য পাওয়া গেছে। একজন চিকিৎসকের অবিলম্বে পরীক্ষা করা উচিত।",
    call_staff_to_kiosk: "কিয়স্কে কর্মী ডাকুন",
    safety_notice_title: "⚠️ রোগীর নিরাপত্তা বিজ্ঞপ্তি",
    safety_notice_desc: "তীব্র বুকে ব্যথা, শ্বাসকষ্ট বা মাথা ঘোরা হলে অবিলম্বে কর্মী সহায়তা নিন।",
    session_details: "সেশনের বিবরণ",
    patient_lbl: "রোগী:",
    patient_id_lbl: "পেশেন্ট আইডি:",
    encounter_id_lbl: "এনকাউন্টার আইডি:",
    language_lbl: "ভাষা:",
    consent_status_lbl: "সম্মতির স্থিতি:",
    back_to_consent: "← সম্মতিতে ফিরে যান",
    proceed_to_docs: "মেডিকেল নথিতে এগিয়ে যান →",

    doc_eyebrow: "ধাপ ৫ / ৬ · মেডিকেল নথি ও OCR",
    doc_title: "রিপোর্ট বা প্রেসক্রিপশন আপলোড করুন",
    doc_subtitle: "ল্যাব রিপোর্ট বা প্রেসক্রিপশন আপলোড করুন। সমর্থিত: PDF, JPG, JPEG, PNG (সর্বোচ্চ ১০ MB)।",
    dropzone_main: "এখানে নথি নির্বাচন করুন বা ফেলুন",
    dropzone_sub: "ফাইল ব্রাউজ করতে ক্লিক করুন",
    run_ocr: "🔍 নেমোট্রন OCR চালান",
    extract_intel: "তথ্য বের করুন →",
    back_to_intake: "← ইনটেকে ফিরে যান",
    proceed_to_summary: "ক্লিনিকাল সারাংশে এগিয়ে যান →",

    summary_eyebrow: "ধাপ ৬ / ৬ · সারাংশ ও জমা",
    summary_title: "ব্যাপক ক্লিনিকাল সারাংশ",
    submit_consultation: "চিকিৎসক পরামর্শের জন্য জমা দিন →",
  }
};

function t(key, defaultVal) {
  const lang = state.language || "en";
  if (I18N[lang] && I18N[lang][key]) {
    return I18N[lang][key];
  }
  if (I18N.en && I18N.en[key]) {
    return I18N.en[key];
  }
  return defaultVal !== undefined ? defaultVal : key;
}


const state = {
  screen: "welcome",
  language: "en",
  patient: null,
  patientId: null,
  encounterId: null,
  consultationId: null,
  consents: [],
  documents: [],
  activeDocumentId: null,
  docInputMode: "file",
  cameraStream: null,
  capturedDocBlob: null,
  capturedDocDataUrl: null,
  activeFhirBundle: null,
  ocrResults: {},
  extractions: {},
  intelligences: {},
  summary: null,
  summaryError: null,
  intake: [],
  redFlags: [],
  voicePreviewText: "",
  isRecording: false,
  pendingVoiceTranscript: "",
  isTranscribing: false,
  recordingSeconds: 0,
  queue: [],
  packet: null,
  backendConnected: false,
};

const appEl = document.querySelector("#app");

function esc(value) {
  if (value === null || value === undefined) return "Unknown";
  return String(value).replace(/[&<>'"]/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", "\"": "&quot;"
  }[c]));
}

function statusBadge(kind, text) {
  return `<div class="message ${kind}"><span>${esc(text)}</span></div>`;
}

function tagHtml(text, type = "automated") {
  return `<span class="tag ${type}">${esc(text)}</span>`;
}

/* =========================================================================
   API CLIENT
   ========================================================================= */

async function api(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeout || API_TIMEOUT);
  
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const response = await fetch(url, { ...options, headers, signal: controller.signal });
    const data = await response.json().catch(() => ({}));
    
    if (!response.ok) {
      let detailMsg = "The request could not be completed.";
      if (typeof data.detail === "string") {
        detailMsg = data.detail;
      } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
        detailMsg = data.detail[0].msg;
      }
      const err = new Error(detailMsg);
      err.status = response.status;
      err.data = data;
      throw err;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      const timeoutErr = new Error("The request took longer than expected. Your saved records remain safe.");
      timeoutErr.status = 504;
      throw timeoutErr;
    }
    if (error instanceof TypeError && error.message.toLowerCase().includes("fetch")) {
      const netErr = new Error("Cannot reach MediKiosk backend at 127.0.0.1:8001. Please check that FastAPI is running.");
      netErr.status = 0;
      throw netErr;
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function checkBackendHealth() {
  try {
    const res = await api("/", { timeout: 4000 });
    state.backendConnected = true;
    const connEl = document.querySelector("#connection-status");
    const lblEl = document.querySelector("#backend-label");
    if (connEl && lblEl) {
      connEl.className = "connection online";
      lblEl.textContent = "Backend :8001 Ready";
    }
  } catch (e) {
    state.backendConnected = false;
    const connEl = document.querySelector("#connection-status");
    const lblEl = document.querySelector("#backend-label");
    if (connEl && lblEl) {
      connEl.className = "connection offline";
      lblEl.textContent = "Backend Offline";
    }
  }
}

function safeProviderErrorMessage(error) {
  if ([502, 503, 504, 0].includes(error.status)) {
    return "AI clinical service is temporarily unavailable. Your visit information has been safely preserved. Please continue with manual physician review.";
  }
  return error.message || "An unexpected error occurred.";
}

function setScreen(screen) {
  stopDocCamera();
  state.screen = screen;
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function getConsentRecord(purpose) {
  return state.consents.find(item => item.purpose === purpose);
}

function isConsentActive(purpose) {
  const c = getConsentRecord(purpose);
  return c !== undefined && c.status === "granted";
}

async function loadPatientConsents() {
  if (!state.patientId) return;
  try {
    const res = await api(`/patients/${state.patientId}/consents`);
    state.consents = res.consents || [];
  } catch (e) {
    console.warn("Could not load consents:", e);
  }
}

function updateLangButton() {
  const btn = document.querySelector("#current-lang-btn");
  if (btn) {
    const current = LANGUAGES.find(l => l.code === state.language) || LANGUAGES[0];
    btn.textContent = `🌐 ${current.label}`;
  }
  const sihEl = document.querySelector(".sih-tag");
  if (sihEl) sihEl.textContent = t("sih_tag", "SIH 2026 Patient Caretaking");

  const portalBtn = document.querySelector(".portal-btn");
  if (portalBtn) portalBtn.textContent = t("portal_btn", "👨‍⚕️ Physician Review");

  const nurseBtn = document.querySelector(".danger-button[data-action='nurse']");
  if (nurseBtn) nurseBtn.textContent = t("call_staff", "🚨 Call Staff");

  const staffH2 = document.querySelector("#staff-dialog h2");
  if (staffH2) staffH2.textContent = t("staff_dialog_title", "Staff Assistance Requested");
  const staffP = document.querySelector("#staff-dialog p");
  if (staffP) staffP.textContent = t("staff_dialog_desc", "Please remain at the kiosk. A hospital staff member is being alerted to your kiosk station.");
  const staffBtn = document.querySelector("#staff-dialog [data-action='close-dialog']");
  if (staffBtn) staffBtn.textContent = t("staff_dialog_btn", "I Understand");
}

/* =========================================================================
   UI HELPERS & STEPPERS
   ========================================================================= */

function renderStepper(stepIdx) {
  const stepKeys = [
    "step_language",
    "step_identity",
    "step_consent",
    "step_intake",
    "step_documents",
    "step_review"
  ];
  return `
    <nav class="stepper" aria-label="Intake progress">
      ${stepKeys.map((key, i) => {
        let cls = "step";
        if (i < stepIdx) cls += " done";
        else if (i === stepIdx) cls += " active";
        return `
          <div class="${cls}">
            <span class="step-num">${i < stepIdx ? "✓" : i + 1}</span>
            <span>${esc(t(key))}</span>
          </div>
        `;
      }).join("")}
    </nav>
  `;
}

/* =========================================================================
   SCREENS
   ========================================================================= */

/* 1. WELCOME */
function renderWelcome() {
  return `
    <section class="page">
      <div class="hero">
        <span class="eyebrow">${esc(t("welcome_eyebrow"))}</span>
        <h1>${esc(t("welcome_title"))}</h1>
        <p class="subtitle">
          ${esc(t("welcome_subtitle"))}
        </p>
        
        <div class="button-row" style="justify-content: center; margin-top: 32px;">
          <button class="primary-button" data-action="start-touch" style="font-size: 17px; padding: 16px 28px;">
            ${esc(t("start_touch"))}
          </button>
          <button class="voice-button" data-action="start-voice" style="font-size: 17px; padding: 16px 28px;">
            ${esc(t("start_voice"))}
          </button>
        </div>

        <div class="privacy-banner">
          <span style="font-size: 20px;">🛡️</span>
          <div>
            <strong>${esc(t("privacy_title"))}:</strong>
            ${esc(t("privacy_desc"))}
          </div>
        </div>
      </div>

      <div class="two-grid" style="margin-top: 32px;">
        <article class="choice-card">
          <span class="eyebrow">${esc(t("kiosk_self_service"))}</span>
          <h2>${esc(t("self_service_title"))}</h2>
          <p>${esc(t("self_service_desc"))}</p>
          <div class="button-row" style="margin-top: 20px;">
            <button class="outline-button" data-action="go-language">${esc(t("select_lang_begin"))}</button>
          </div>
        </article>

        <article class="choice-card">
          <span class="eyebrow">${esc(t("physician_team"))}</span>
          <h2>${esc(t("portal_btn"))}</h2>
          <p>Inspect incoming patient packets, review uploaded source documents and raw OCR, verify clinical observations, and complete sign-off audits.</p>
          <div class="button-row" style="margin-top: 20px;">
            <button class="quiet-button" data-action="physician" style="font-weight: 700;">${esc(t("open_physician_workspace"))}</button>
          </div>
        </article>
      </div>
    </section>
  `;
}

/* 2. LANGUAGE */
function renderLanguage() {
  return `
    <section class="page">
      ${renderStepper(0)}
      <div class="panel">
        <span class="eyebrow">${esc(t("lang_eyebrow"))}</span>
        <h1 style="font-size: 28px; margin: 8px 0 6px;">${esc(t("lang_title"))}</h1>
        <p class="muted">${esc(t("lang_subtitle"))}</p>

        <div class="lang-tier-title">
          <span>🇮🇳</span> Fully Localized Kiosk Interface &amp; Clinical Voice (5 Primary Languages)
        </div>
        <div class="lang-grid">
          ${LANGUAGES.filter(l => l.tier === "full").map(lang => {
            const isSelected = state.language === lang.code;
            return `
              <button class="choice-card lang-card-mini ${isSelected ? "selected" : ""}" data-action="select-lang" data-code="${lang.code}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                  <h2 style="font-size: 20px;">${esc(lang.native)}</h2>
                  ${isSelected ? `<span class="tag verified" style="font-size: 11px;">✓ Selected</span>` : `<span class="tag" style="font-size: 10px; background: #e0f2fe; color: #0369a1;">Full UI</span>`}
                </div>
                <p style="font-weight: 600; color: var(--ink-light); margin-top: 4px; font-size: 14px;">${esc(lang.label)}</p>
                <p style="font-size: 12.5px; margin-top: 2px;">${esc(lang.sub)}</p>
              </button>
            `;
          }).join("")}
        </div>

        <div class="lang-tier-title" style="margin-top: 28px;">
          <span>🎙️</span> 17 Scheduled Languages of India — Speech-Assisted Intake (Groq Whisper Multilingual)
        </div>
        <p class="muted" style="font-size: 13.5px; margin-bottom: 12px;">
          Patients may speak naturally in any of the 22 Eighth Schedule languages. Audio is captured and transcribed via high-accuracy Whisper speech intelligence.
        </p>
        <div class="lang-grid">
          ${LANGUAGES.filter(l => l.tier === "speech").map(lang => {
            const isSelected = state.language === lang.code;
            return `
              <button class="choice-card lang-card-mini ${isSelected ? "selected" : ""}" data-action="select-lang" data-code="${lang.code}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                  <h3 style="font-size: 17px;">${esc(lang.native)}</h3>
                  ${isSelected ? `<span class="tag verified" style="font-size: 11px;">✓ Selected</span>` : `<span class="tag automated" style="font-size: 10px;">Whisper</span>`}
                </div>
                <p style="font-weight: 600; color: var(--ink-light); margin-top: 2px; font-size: 13.5px;">${esc(lang.label)}</p>
                <p style="font-size: 12px; margin-top: 2px;">${esc(lang.sub)}</p>
              </button>
            `;
          }).join("")}
        </div>

        <div class="button-row" style="margin-top: 32px; justify-content: space-between;">
          <button class="outline-button" data-action="home">${esc(t("back_to_welcome"))}</button>
          <button class="primary-button" data-action="go-identity">${esc(t("continue_to_identity"))}</button>
        </div>
      </div>
    </section>
  `;
}

/* 3. PATIENT IDENTIFICATION & REGISTRATION */
function renderIdentity() {
  return `
    <section class="page">
      ${renderStepper(1)}
      <div class="panel">
        <span class="eyebrow">${esc(t("id_eyebrow"))}</span>
        <h1 style="font-size: 28px; margin: 8px 0 6px;">${esc(t("id_title"))}</h1>
        <p class="muted">${esc(t("id_subtitle"))}</p>

        <div class="two-grid" style="margin-top: 24px;">
          <!-- RETURNING PATIENT -->
          <form id="existing-patient-form" class="choice-card" style="justify-content: flex-start;">
            <span class="eyebrow" style="color: var(--blue-primary);">${esc(t("returning_patient"))}</span>
            <h2 style="font-size: 20px;">${esc(t("have_patient_id"))}</h2>
            <p style="margin-bottom: 16px;">${esc(t("returning_desc"))}</p>
            
            <label for="existing-id-input">
              ${esc(t("patient_id_input_label"))}
              <input id="existing-id-input" name="patient_id" type="number" min="1" required placeholder="e.g. 1" autocomplete="off">
            </label>

            <div class="button-row" style="margin-top: 20px;">
              <button type="submit" class="outline-button" style="width: 100%;">
                ${esc(t("lookup_record_btn"))}
              </button>
            </div>
            <div id="existing-status-box" style="margin-top: 14px;"></div>
          </form>

          <!-- NEW PATIENT REGISTRATION -->
          <form id="new-patient-form" class="choice-card" style="justify-content: flex-start;">
            <span class="eyebrow" style="color: var(--teal-primary);">${esc(t("new_patient_reg"))}</span>
            <h2 style="font-size: 20px;">${esc(t("first_time_title"))}</h2>
            <p style="margin-bottom: 16px;">${esc(t("first_time_desc"))}</p>

            <label for="reg-name-input">
              ${esc(t("full_name"))}
              <input id="reg-name-input" name="name" type="text" minlength="2" maxlength="100" required placeholder="e.g. Aarav Sharma" autocomplete="name">
            </label>

            <div class="two-col">
              <label for="reg-age-input">
                ${esc(t("age"))}
                <input id="reg-age-input" name="age" type="number" min="0" max="120" required placeholder="e.g. 35">
              </label>

              <label for="reg-gender-select">
                ${esc(t("gender"))}
                <select id="reg-gender-select" name="gender">
                  <option value="not_specified">${esc(t("gender_unspecified"))}</option>
                  <option value="female">${esc(t("gender_female"))}</option>
                  <option value="male">${esc(t("gender_male"))}</option>
                  <option value="other">${esc(t("gender_other"))}</option>
                </select>
              </label>
            </div>

            <label for="reg-phone-input">
              ${esc(t("mobile_number"))}
              <input id="reg-phone-input" name="phone" type="tel" maxlength="20" placeholder="+91 9876543210" autocomplete="tel">
            </label>

            <label for="reg-abha-input">
              ${esc(t("abha_number"))}
              <input id="reg-abha-input" name="abha_id" type="text" maxlength="32" placeholder="e.g. 12-3456-7890-1234">
            </label>

            <div class="button-row" style="margin-top: 24px;">
              <button type="submit" class="primary-button" style="width: 100%;">
                ${esc(t("create_patient_btn"))}
              </button>
            </div>
            <div id="new-status-box" style="margin-top: 14px;"></div>
          </form>
        </div>

        <div class="button-row" style="margin-top: 28px;">
          <button class="outline-button" data-action="go-language">${esc(t("back_to_language"))}</button>
        </div>
      </div>
    </section>
  `;
}

/* 4. CONSENT */
function renderConsent() {
  const patientName = state.patient?.name || "Patient";
  return `
    <section class="page">
      ${renderStepper(2)}
      <div class="panel">
        <span class="eyebrow">${esc(t("consent_eyebrow"))}</span>
        <h1 style="font-size: 28px; margin: 8px 0 6px;">${esc(t("consent_title"))}</h1>
        <p class="muted">
          ${esc(t("patient_lbl"))} <strong>${esc(patientName)}</strong> (ID #${esc(state.patientId)}).
          ${esc(t("consent_subtitle"))}
        </p>

        <div style="margin-top: 24px;">
          ${PURPOSES.map(p => {
            const consentRec = getConsentRecord(p.key);
            const isActive = consentRec && consentRec.status === "granted";
            const isRevoked = consentRec && consentRec.status === "revoked";
            
            let statusBadgeHtml = `<span class="status pending">${esc(t("status_not_granted", "Not Granted"))}</span>`;
            let actionBtnHtml = `
              <button class="primary-button" data-action="grant-consent" data-purpose="${p.key}" style="min-height: 38px; padding: 8px 18px; font-size: 14px;">
                ${esc(t("grant_consent_btn", "✓ Grant Consent"))}
              </button>
            `;

            if (isActive) {
              statusBadgeHtml = `<span class="status verified" style="font-weight: 700;">● Active — Granted</span>`;
              actionBtnHtml = `
                <button class="outline-button" data-action="revoke-consent" data-consent-id="${consentRec.id}" data-purpose="${p.key}" style="min-height: 38px; padding: 8px 18px; font-size: 14px; color: var(--red-primary); border-color: #fca5a5;">
                  ${esc(t("revoke_consent_btn", "✕ Revoke Consent"))}
                </button>
              `;
            } else if (isRevoked) {
              statusBadgeHtml = `<span class="status urgent" style="font-weight: 700;">✕ Revoked</span>`;
              actionBtnHtml = `
                <button class="primary-button" data-action="grant-consent" data-purpose="${p.key}" style="min-height: 38px; padding: 8px 18px; font-size: 14px; background: var(--blue-primary);">
                  ↺ Grant Again
                </button>
              `;
            }

            const pTitle = t("purpose_" + p.key + "_title", p.title);
            const pDesc = t("purpose_" + p.key + "_desc", p.desc);

            const abdmHeader = p.isAbdm ? `
              <div style="margin: 26px 0 12px; padding: 14px 18px; background: #f0fdf4; border: 1.5px solid #86efac; border-radius: var(--radius-md);">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 20px;">🛡️</span>
                  <strong style="color: #166534; font-size: 15px;">ABDM Integration — OPTIONAL &amp; SEPARATED FROM IN-CLINIC CARE</strong>
                </div>
                <p style="font-size: 13.5px; color: #14532d; margin-top: 4px;">
                  Ayushman Bharat Digital Mission record sharing is strictly voluntary. You do NOT need ABDM consent to receive full OPD care today.
                </p>
              </div>
            ` : "";

            return `
              ${abdmHeader}
              <div class="consent-item ${isActive ? "active-consent" : ""} ${p.isAbdm ? "abdm-purpose" : ""}">
                <div class="consent-head">
                  <div>
                    <h3>${esc(pTitle)} ${p.requiredForIntake ? `<span class="tag urgent" style="font-size: 10px;">Required</span>` : p.isAbdm ? `<span class="tag" style="font-size: 10px; background: #e0f2fe; color: #0369a1;">Optional</span>` : ""}</h3>
                  </div>
                  <div>
                    ${statusBadgeHtml}
                  </div>
                </div>

                <div class="consent-desc">${esc(pDesc)}</div>

                <div class="button-row" style="margin-top: 12px;">
                  ${actionBtnHtml}
                </div>
              </div>
            `;
          }).join("")}
        </div>

        <div id="consent-feedback" style="margin-top: 16px;"></div>

        <div class="button-row" style="margin-top: 28px; justify-content: space-between;">
          <button class="outline-button" data-action="go-identity">${esc(t("change_patient_btn"))}</button>
          <button class="primary-button" data-action="start-intake-session" style="font-size: 16px;">
            ${esc(t("save_start_intake_btn"))}
          </button>
        </div>
      </div>
    </section>
  `;
}

/* 5. CLINICAL HISTORY INTAKE */
function renderIntake() {
  const patientName = state.patient?.name || "Patient";
  const firstName = patientName.split(" ")[0];
  const urgentBanner = state.redFlags.length ? `
    <div class="message error" style="margin-bottom: 20px; border-width: 2px;">
      <div style="font-size: 24px;">🚨</div>
      <div>
        <strong style="font-size: 16px; color: #991b1b;">${esc(t("urgent_banner_title"))}</strong>
        <p style="margin-top: 4px;">
          ${esc(t("urgent_banner_desc"))}
        </p>
        <div class="button-row" style="margin-top: 12px;">
          <button class="danger-button" data-action="nurse">${esc(t("call_staff_to_kiosk"))}</button>
          <button class="outline-button" data-action="go-documents">${esc(t("proceed_to_docs"))}</button>
        </div>
      </div>
    </div>
  ` : "";

  return `
    <section class="page">
      ${renderStepper(3)}
      ${urgentBanner}

      <div class="two-grid" style="grid-template-columns: 1.8fr 1fr; align-items: start;">
        <!-- MAIN CONVERSATION COLUMN -->
        <div class="panel">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="eyebrow">${esc(t("intake_eyebrow"))}</span>
            <span class="tag automated">Encounter #${esc(state.encounterId || "Pending")}</span>
          </div>

          <h1 style="font-size: 26px; margin: 8px 0 4px;">${esc(t("hello_prefix"))}, ${esc(firstName)}</h1>
          <p class="muted">${esc(t("intake_inst"))}</p>

          <div class="conversation-box" id="conversation-container">
            ${state.intake.map(msg => `
              <div class="bubble ${msg.role}">
                <span class="bubble-tag">${msg.role === "assistant" ? "MediKiosk Assistant" : "You"}</span>
                ${esc(msg.text)}
              </div>
            `).join("")}
          </div>

          <!-- GROQ WHISPER PROCESSING BANNER -->
          ${state.isTranscribing ? `
            <div class="voice-transcribing-banner">
              <div class="pulse-ring"></div>
              <div style="margin-left: 14px;">
                <strong style="color: var(--teal-dark); font-size: 16px;">${esc(t("groq_whisper_processing"))}</strong>
                <p class="muted" style="margin: 2px 0 0;">${esc(t("groq_whisper_transcribing"))} ${esc(state.language.toUpperCase())}…</p>
              </div>
            </div>
          ` : ""}

          <!-- PATIENT CONFIRMATION CARD -->
          ${state.pendingVoiceTranscript ? `
            <div class="voice-confirmation-card" id="voice-confirmation-card">
              <div class="voice-confirm-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span class="whisper-pill">${esc(t("whisper_pill"))}</span>
                  <span class="tag verified" style="font-size: 11px;">${esc(t("patient_review_badge"))}</span>
                </div>
                <span class="muted" style="font-size: 13px;">${esc(t("whisper_confirm_hint"))}</span>
              </div>
              <textarea
                id="voice-confirmed-text"
                rows="3"
                class="voice-confirm-textarea"
                placeholder="Review or edit your spoken words here..."
              >${esc(state.pendingVoiceTranscript)}</textarea>
              <div class="button-row" style="margin-top: 12px; justify-content: flex-end; gap: 10px;">
                <button type="button" class="outline-button" data-action="rerecord-voice">
                  ${esc(t("rerecord_btn"))}
                </button>
                <button type="button" class="primary-button" data-action="confirm-send-voice" style="background: var(--teal-primary);">
                  ${esc(t("confirm_send_btn"))}
                </button>
              </div>
            </div>
          ` : ""}

          <!-- INPUT FORM -->
          <form id="intake-chat-form" style="margin-top: 12px;">
            <textarea
              id="intake-message-input"
              rows="3"
              required
              maxlength="4000"
              placeholder="${esc(t("chat_placeholder"))}"
            >${esc(state.voicePreviewText)}</textarea>

            <div class="button-row" style="margin-top: 12px; justify-content: space-between;">
              <button
                type="button"
                id="mic-btn"
                class="voice-button ${state.isRecording ? "recording" : ""}"
                data-action="${state.isRecording ? "stop-recording" : "start-recording"}"
              >
                ${state.isRecording ? `${esc(t("stop_recording"))} (<span id="recording-timer">${String(Math.floor((state.recordingSeconds || 0) / 60)).padStart(2, "0")}:${String((state.recordingSeconds || 0) % 60).padStart(2, "0")}</span>)` : esc(t("speak_mic"))}
              </button>

              <button type="submit" class="primary-button">
                ${esc(t("send_answer"))}
              </button>
            </div>
          </form>

          <div id="intake-status-feedback" style="margin-top: 12px;"></div>

          <div class="button-row" style="margin-top: 24px; border-top: 1px solid var(--line); padding-top: 18px; justify-content: space-between;">
            <button class="outline-button" data-action="go-consent">${esc(t("back_to_consent"))}</button>
            <button class="primary-button" data-action="go-documents">${esc(t("proceed_to_docs"))}</button>
          </div>
        </div>

        <!-- RIGHT SIDEBAR: VISIT CONTEXT & SAFETY -->
        <div>
          <div class="panel" style="margin-bottom: 20px;">
            <span class="eyebrow">${esc(t("session_details"))}</span>
            <div style="margin-top: 14px; font-size: 14px;">
              <p style="margin-bottom: 8px;"><strong>${esc(t("patient_lbl"))}</strong> ${esc(patientName)}</p>
              <p style="margin-bottom: 8px;"><strong>${esc(t("patient_id_lbl"))}</strong> #${esc(state.patientId)}</p>
              <p style="margin-bottom: 8px;"><strong>${esc(t("encounter_id_lbl"))}</strong> #${esc(state.encounterId || "Creating…")}</p>
              <p style="margin-bottom: 8px;"><strong>${esc(t("language_lbl"))}</strong> ${esc(state.language.toUpperCase())}</p>
              <p><strong>${esc(t("consent_status_lbl"))}</strong> ${isConsentActive("clinical_history") ? `<span class="tag verified">${esc(t("status_active"))}</span>` : `<span class="tag urgent">${esc(t("status_not_granted"))}</span>`}</p>
            </div>
          </div>

          <div class="panel" style="background: #fffbeb; border-color: #fde68a;">
            <h3 style="color: #92400e; font-size: 16px; margin-bottom: 8px;">${esc(t("safety_notice_title"))}</h3>
            <p style="font-size: 13.5px; color: #78350f; line-height: 1.5;">
              ${esc(t("safety_notice_desc"))}
            </p>
          </div>
        </div>
      </div>
    </section>
  `;
}

/* 6. DOCUMENT UPLOAD & OCR */
function renderDocuments() {
  const patientName = state.patient?.name || "Patient";
  return `
    <section class="page">
      ${renderStepper(4)}
      <div class="panel">
        <span class="eyebrow">${esc(t("doc_eyebrow"))}</span>
        <h1 style="font-size: 28px; margin: 8px 0 6px;">${esc(t("doc_title"))}</h1>
        <p class="muted">
          ${esc(t("doc_subtitle"))}
        </p>

        <!-- DOCUMENT INPUT SELECTOR: FILE UPLOAD vs CAMERA SCAN -->
        <div class="doc-tab-bar">
          <button type="button" class="doc-tab-btn ${state.docInputMode !== "camera" ? "active" : ""}" data-action="set-doc-mode" data-mode="file">
            📁 Upload Document File (PDF / Image)
          </button>
          <button type="button" class="doc-tab-btn ${state.docInputMode === "camera" ? "active" : ""}" data-action="set-doc-mode" data-mode="camera">
            📷 Scan with Kiosk Camera
          </button>
        </div>

        ${state.docInputMode === "camera" ? `
          <!-- CAMERA VIEWFINDER & SCANNER -->
          <div class="camera-container">
            ${state.capturedDocDataUrl ? `
              <img id="camera-preview-captured" class="camera-preview-captured" src="${state.capturedDocDataUrl}" alt="Captured document preview">
              <div class="button-row" style="margin-top: 14px; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <button type="button" class="outline-button" data-action="retake-camera-doc" style="color: #fff; border-color: rgba(255,255,255,0.5);">
                  ↺ Retake Document Photo
                </button>
                <button type="button" class="primary-button" data-action="confirm-upload-camera-doc" style="background: var(--teal-primary);">
                  ✓ Use Photo &amp; Analyze with Nemotron OCR
                </button>
              </div>
            ` : `
              <div style="position: relative; width: 100%; max-width: 640px;">
                <video id="camera-video-stream" class="camera-viewfinder" autoplay playsinline muted></video>
                <div class="camera-guide-overlay">
                  <span class="camera-guide-text">Align prescription or report within frame</span>
                </div>
              </div>
              <div class="button-row" style="margin-top: 14px; gap: 12px; justify-content: center;">
                <button type="button" class="primary-button" data-action="capture-camera-doc" style="font-size: 15px; padding: 10px 24px; background: var(--teal-primary);">
                  📸 Snap Document Photo
                </button>
              </div>
            `}
          </div>
        ` : `
          <!-- DROPZONE / UPLOAD FORM -->
          <form id="doc-upload-form">
            <div class="upload-dropzone" id="dropzone-box" onclick="document.querySelector('#file-input').click()">
              <div class="upload-icon">📄</div>
              <strong style="font-size: 18px; color: var(--ink);">${esc(t("dropzone_main"))}</strong>
              <p class="muted" style="margin-top: 6px;">${esc(t("dropzone_sub"))}</p>
              <input id="file-input" type="file" accept="application/pdf,image/jpeg,image/png">
            </div>

            <div id="file-chosen-notice" style="margin-top: 12px; display: none;" class="message info">
              <span id="file-chosen-name">No file chosen</span>
              <button type="submit" class="primary-button" style="margin-left: auto; min-height: 38px; padding: 6px 16px;">${esc(t("upload_file_btn"))}</button>
            </div>
          </form>
        `}

        <div id="upload-feedback" style="margin-top: 14px;"></div>

        <!-- UPLOADED DOCUMENTS LIST -->
        <div style="margin-top: 32px;">
          <h2 style="font-size: 20px; margin-bottom: 14px;">${esc(t("uploaded_docs_title"))}</h2>
          ${state.documents.length === 0 ? `
            <div class="choice-card" style="text-align: center; padding: 32px; background: #f8fafc;">
              <p class="muted">${esc(t("no_docs_uploaded"))}</p>
            </div>
          ` : `
            <div style="display: grid; gap: 14px;">
              ${state.documents.map(doc => {
                const ocrData = state.ocrResults[doc.id];
                const hasOcr = Boolean(ocrData);
                const hasExtract = Boolean(state.extractions[doc.id]);

                return `
                  <div class="consent-item" style="border-left: 4px solid var(--teal-primary);">
                    <div class="consent-head">
                      <div>
                        <h3>📄 ${esc(doc.file_name || doc.filename)}</h3>
                        <p class="muted" style="font-size: 13px; margin-top: 4px;">
                          Document #${esc(doc.id)} · Size: ${(doc.file_size / 1024).toFixed(1)} KB · Status: <strong>${esc(doc.ocr_status)}</strong>
                        </p>
                      </div>
                      <div>
                        <span class="status ${doc.ocr_status === "completed" ? "verified" : doc.ocr_status === "failed" ? "urgent" : "pending"}">
                          ${esc(doc.ocr_status)}
                        </span>
                      </div>
                    </div>

                    ${hasOcr ? `
                      <div style="margin-top: 14px; background: #f8fafc; padding: 12px 14px; border-radius: var(--radius-sm); border: 1px solid var(--line);">
                        <strong style="font-size: 13px; color: var(--teal-dark);">Extracted OCR Text Preview (NVIDIA Nemotron OCR v2):</strong>
                        <pre style="white-space: pre-wrap; font-size: 13px; color: var(--ink-light); margin: 6px 0 0; max-height: 140px; overflow-y: auto;">${esc(ocrData.text || ocrData.extracted_text || "(No text recognized in image)")}</pre>
                      </div>
                    ` : ""}

                    <div class="button-row" style="margin-top: 14px;">
                      <button
                        class="outline-button"
                        data-action="run-ocr"
                        data-doc-id="${doc.id}"
                        style="min-height: 38px; padding: 6px 14px; font-size: 13.5px;"
                      >
                        🔍 ${hasOcr ? "Re-run Nemotron OCR" : "Run Nemotron OCR"}
                      </button>

                      ${hasOcr ? `
                        <button
                          class="primary-button"
                          data-action="run-extract"
                          data-doc-id="${doc.id}"
                          style="min-height: 38px; padding: 6px 14px; font-size: 13.5px;"
                        >
                          ⚡ View Structured Information &amp; Intelligence →
                        </button>
                      ` : ""}
                    </div>
                  </div>
                `;
              }).join("")}
            </div>
          `}
        </div>

        <div class="button-row" style="margin-top: 32px; justify-content: space-between;">
          <button class="outline-button" data-action="go-intake">${esc(t("back_to_intake"))}</button>
          <div class="button-row">
            <button class="outline-button" data-action="go-abdm">${esc(t("abha_abdm_sharing"))}</button>
            <button class="primary-button" data-action="go-summary">${esc(t("proceed_to_summary"))}</button>
          </div>
        </div>
      </div>
    </section>
  `;
}

/* 7. STRUCTURED INFORMATION & TIMELINE */
function renderStructured() {
  const docId = state.activeDocumentId;
  const extraction = state.extractions[docId]?.extraction;
  const intelligence = state.intelligences[docId];

  if (!extraction) {
    return `
      <section class="page">
        <div class="panel">
          <span class="eyebrow">STRUCTURED EXTRACTION</span>
          <h1>Structured Information Unavailable</h1>
          <p class="muted">No extraction record was retrieved for Document #${esc(docId)}.</p>
          <div class="button-row" style="margin-top: 24px;">
            <button class="primary-button" data-action="go-documents">← Back to Documents</button>
          </div>
        </div>
      </section>
    `;
  }

  const observations = extraction.observations || [];
  const medications = extraction.medications || [];
  const allergies = extraction.allergies || [];
  const conditions = extraction.diagnoses_or_conditions || [];
  const timelineEvents = intelligence?.timeline?.[0]?.events || [];

  return `
    <section class="page">
      <div class="panel">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
          <div>
            <span class="eyebrow">DOCUMENT INTELLIGENCE</span>
            <h1 style="font-size: 28px; margin: 6px 0;">Structured Medical Information</h1>
            <p class="muted">Source: Document #${esc(docId)} · Processed from verified OCR text</p>
          </div>
          ${tagHtml("AI / AUTOMATED / EXTRACTED — NOT PHYSICIAN VERIFIED", "automated")}
        </div>

        <!-- OBSERVATIONS TABLE -->
        <div style="margin-top: 28px;">
          <h2 style="font-size: 20px; margin-bottom: 12px;">Laboratory &amp; Clinical Observations</h2>
          ${observations.length === 0 ? `
            <p class="muted">No clinical observations were explicitly listed in this document.</p>
          ` : `
            <table class="med-table">
              <thead>
                <tr>
                  <th>Test / Observation</th>
                  <th>Observed Value</th>
                  <th>Unit</th>
                  <th>Reference Range</th>
                  <th>Status Status</th>
                  <th>Source Text</th>
                </tr>
              </thead>
              <tbody>
                ${observations.map(obs => {
                  let statusCls = "pending";
                  if (obs.status === "normal") statusCls = "verified";
                  else if (obs.status === "high" || obs.status === "low") statusCls = "urgent";
                  return `
                    <tr>
                      <td><strong>${esc(obs.name)}</strong></td>
                      <td>${esc(obs.value || "Unknown")}</td>
                      <td>${esc(obs.unit || "—")}</td>
                      <td>${esc(obs.reference_range || "—")}</td>
                      <td><span class="status ${statusCls}">${esc(obs.status || "Unknown")}</span></td>
                      <td><small class="muted">${esc(obs.source_text || "—")}</small></td>
                    </tr>
                  `;
                }).join("")}
              </tbody>
            </table>
          `}
        </div>

        <!-- MEDICATIONS & ALLERGIES -->
        <div class="two-grid" style="margin-top: 24px;">
          <div class="panel" style="background: #f8fafc;">
            <h3 style="font-size: 18px; margin-bottom: 12px;">Prescribed Medications</h3>
            ${medications.length === 0 ? `<p class="muted">None explicitly extracted.</p>` : `
              <ul style="margin: 0; padding-left: 20px;">
                ${medications.map(m => `
                  <li style="margin-bottom: 6px;">
                    <strong>${esc(m.name)}</strong> — ${esc(m.dose || "")} ${esc(m.frequency || "")}
                    ${m.source_text ? `<br><small class="muted">"${esc(m.source_text)}"</small>` : ""}
                  </li>
                `).join("")}
              </ul>
            `}
          </div>

          <div class="panel" style="background: #f8fafc;">
            <h3 style="font-size: 18px; margin-bottom: 12px;">Reported Allergies</h3>
            ${allergies.length === 0 ? `<p class="muted">None explicitly noted in document.</p>` : `
              <ul style="margin: 0; padding-left: 20px;">
                ${allergies.map(a => `
                  <li style="margin-bottom: 6px;">
                    <strong>${esc(a.substance)}</strong>: ${esc(a.reaction || "Reaction not specified")}
                  </li>
                `).join("")}
              </ul>
            `}
          </div>
        </div>

        <!-- EXPLICIT CONDITIONS -->
        <div class="panel" style="margin-top: 20px; background: #f8fafc;">
          <h3 style="font-size: 18px; margin-bottom: 8px;">Explicit Conditions / Diagnoses Noted in Source</h3>
          <p class="muted" style="font-size: 13px; margin-bottom: 12px;">
            ⚠️ These are existing conditions transcribed strictly from your uploaded report, NOT a new diagnosis formed by this kiosk.
          </p>
          ${conditions.length === 0 ? `<p class="muted">No explicit conditions recorded in document text.</p>` : `
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              ${conditions.map(c => `<span class="tag" style="background: #e2e8f0; color: #1e293b;">${esc(c.text || c)}</span>`).join("")}
            </div>
          `}
        </div>

        <!-- TIMELINE -->
        ${timelineEvents.length > 0 ? `
          <div class="panel" style="margin-top: 20px; background: #f8fafc;">
            <h3 style="font-size: 18px; margin-bottom: 12px;">Medical Timeline</h3>
            <ul style="margin: 0; padding-left: 20px;">
              ${timelineEvents.map(evt => `
                <li style="margin-bottom: 6px;">
                  <strong>${esc(evt.date || "Undated")}:</strong> ${esc(evt.event)} <small class="muted">(${esc(evt.source || "Document")})</small>
                </li>
              `).join("")}
            </ul>
          </div>
        ` : ""}

        <div class="button-row" style="margin-top: 32px; justify-content: space-between;">
          <button class="outline-button" data-action="go-documents">← Back to Documents</button>
          <button class="primary-button" data-action="go-summary">Proceed to Clinical Summary →</button>
        </div>
      </div>
    </section>
  `;
}

/* 8. CLINICAL SUMMARY */
function renderSummary() {
  const patientName = state.patient?.name || "Patient";
  const summaryData = state.summary?.generated_summary;
  const isAiSummaryAvailable = Boolean(summaryData);

  return `
    <section class="page">
      ${renderStepper(5)}
      <div class="panel">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
          <div>
            <span class="eyebrow">${esc(t("summary_eyebrow"))}</span>
            <h1 style="font-size: 28px; margin: 6px 0;">${esc(t("summary_title"))}</h1>
            <p class="muted">${esc(t("patient_lbl"))} <strong>${esc(patientName)}</strong> · ${esc(t("encounter_id_lbl"))} #${esc(state.encounterId || "Unknown")}</p>
          </div>
          ${isAiSummaryAvailable ? tagHtml("AI-GENERATED SUMMARY — NOT PHYSICIAN VERIFIED", "automated") : ""}
        </div>

        ${!isAiSummaryAvailable ? `
          <div class="message warning" style="margin-top: 20px;">
            <span style="font-size: 20px;">ℹ️</span>
            <div>
              <strong>AI Clinical Summary Service is Unavailable:</strong>
              ${esc(state.summaryError || "Upstream AI service could not be reached. All patient answers and source documents are compiled below from direct kiosk records.")}
            </div>
          </div>
        ` : ""}

        <!-- SUMMARY CONTENT -->
        <div class="two-grid" style="margin-top: 24px;">
          <!-- LEFT COLUMN -->
          <div style="display: grid; gap: 20px;">
            ${summaryData?.summary ? `
              <div class="panel" style="background: #f0fdf4; border: 1px solid #bbf7d0;">
                <h3 style="font-size: 17px; margin-bottom: 8px; color: #166534; display: flex; align-items: center; gap: 6px;">
                  <span>🤖</span> <span>AI Clinical Narrative Synthesis</span>
                </h3>
                <p style="font-size: 14.5px; color: #1e293b; line-height: 1.6; margin: 0;">
                  ${esc(summaryData.summary)}
                </p>
              </div>
            ` : ""}

            <div class="panel" style="background: #f8fafc;">
              <h3 style="font-size: 18px; margin-bottom: 8px;">${esc(t("summary_hpi_title"))}</h3>
              <p style="font-size: 15px; color: var(--ink-light); line-height: 1.6;">
                ${esc(summaryData?.history_of_present_illness || (state.intake.filter(m => m.role === "user").map(m => m.text).join(" ") || "Patient-reported intake details recorded in session."))}
              </p>
            </div>

            <div class="panel" style="background: #f8fafc;">
              <h3 style="font-size: 18px; margin-bottom: 8px;">${esc(t("summary_symptoms_title"))}</h3>
              ${(summaryData?.symptoms || []).length > 0 ? `
                <ul style="margin: 0; padding-left: 20px;">
                  ${summaryData.symptoms.map(s => `
                    <li><strong>${esc(s.name)}:</strong> ${esc(s.details || "Reported")}</li>
                  `).join("")}
                </ul>
              ` : `
                <p class="muted">${state.redFlags.length ? "Potential urgent symptom flagged during intake." : "No severe red flags noted."}</p>
              `}
            </div>
          </div>

          <!-- RIGHT COLUMN -->
          <div style="display: grid; gap: 20px;">
            <div class="panel" style="background: #f8fafc;">
              <h3 style="font-size: 18px; margin-bottom: 8px;">${esc(t("summary_meds_allergies_title"))}</h3>
              <p style="font-size: 14px; margin-bottom: 6px;"><strong>${esc(t("medications_lbl"))}</strong></p>
              ${(summaryData?.medications || []).length > 0 ? `
                <ul style="margin: 0; padding-left: 20px;">
                  ${summaryData.medications.map(m => `<li>${esc(m.name)} ${esc(m.dose || "")}</li>`).join("")}
                </ul>
              ` : `<p class="muted" style="margin-bottom: 12px;">No active medications noted.</p>`}

              <p style="font-size: 14px; margin-top: 12px; margin-bottom: 6px;"><strong>Allergies:</strong></p>
              ${(summaryData?.allergies || []).length > 0 ? `
                <ul style="margin: 0; padding-left: 20px;">
                  ${summaryData.allergies.map(a => `<li>${esc(a.substance)} (${esc(a.reaction || "Reaction not specified")})</li>`).join("")}
                </ul>
              ` : `<p class="muted">No known drug allergies reported.</p>`}
            </div>

            <div class="panel" style="background: #f8fafc;">
              <h3 style="font-size: 18px; margin-bottom: 8px;">Source Document Findings</h3>
              <p style="font-size: 14px; color: var(--ink-light);">
                Total Documents Uploaded: <strong>${state.documents.length}</strong>
              </p>
              ${state.documents.map(d => `
                <div style="font-size: 13.5px; margin-top: 6px;">
                  📄 Document #${esc(d.id)} (${esc(d.file_name)}) — Status: <strong>${esc(d.ocr_status)}</strong>
                </div>
              `).join("")}
            </div>
          </div>
        </div>

        <div class="button-row" style="margin-top: 32px; justify-content: space-between;">
          <button class="outline-button" data-action="go-documents">${esc(t("back_to_docs"))}</button>
          <button class="primary-button" data-action="go-review" style="font-size: 16px;">
            ${esc(t("review_submit_visit"))}
          </button>
        </div>
      </div>
    </section>
  `;
}

/* 9. PATIENT FINAL REVIEW */
function renderReview() {
  const patientName = state.patient?.name || "Patient";
  return `
    <section class="page">
      <div class="panel">
        <span class="eyebrow">${esc(t("review_eyebrow"))}</span>
        <h1 style="font-size: 28px; margin: 8px 0 6px;">${esc(t("review_title"))}</h1>
        <p class="muted">${esc(t("review_subtitle"))}</p>

        <div class="two-grid" style="margin-top: 24px;">
          <div class="choice-card" style="background: #f8fafc;">
            <h3>${esc(t("patient_demographics"))}</h3>
            <p style="margin-top: 10px;"><strong>${esc(t("full_name"))}:</strong> ${esc(patientName)}</p>
            <p><strong>${esc(t("age"))} / ${esc(t("gender"))}:</strong> ${esc(state.patient?.age)} yrs / ${esc(state.patient?.gender)}</p>
            <p><strong>${esc(t("mobile_number"))}:</strong> ${esc(state.patient?.phone || "Not provided")}</p>
            <p><strong>${esc(t("abha_number"))}:</strong> ${esc(state.patient?.abha_id || "Not linked")}</p>
          </div>

          <div class="choice-card" style="background: #f8fafc;">
            <h3>${esc(t("visit_overview"))}</h3>
            <p style="margin-top: 10px;"><strong>${esc(t("encounter_id_lbl"))}</strong> #${esc(state.encounterId || "Active")}</p>
            <p><strong>Uploaded Files:</strong> ${state.documents.length} report(s)</p>
            <p><strong>Clinical History Consent:</strong> ${isConsentActive("clinical_history") ? `<span class="tag verified">${esc(t("status_active"))}</span>` : `<span class="tag urgent">${esc(t("status_revoked"))}</span>`}</p>
            <p><strong>ABDM Sharing Consent:</strong> ${isConsentActive("abdm_sharing") ? `<span class="tag verified">${esc(t("status_active"))}</span>` : `<span class="tag pending">${esc(t("status_not_granted"))}</span>`}</p>
          </div>
        </div>

        <div class="alert-box urgent-note" style="margin-top: 24px;">
          <strong>${esc(t("affirmation_lbl"))}</strong> ${esc(t("affirmation_note"))}
        </div>

        <div id="submit-feedback" style="margin-top: 16px;"></div>

        <div class="button-row" style="margin-top: 28px; justify-content: space-between;">
          <button class="outline-button" data-action="go-summary">${esc(t("back_to_summary"))}</button>
          <button class="primary-button" data-action="submit-final-visit" style="font-size: 17px; padding: 14px 28px;">
            ${esc(t("submit_final_visit_btn"))}
          </button>
        </div>
      </div>
    </section>
  `;
}

/* 10. SUCCESS */
function renderSuccess() {
  return `
    <section class="page">
      <div class="hero">
        <div style="font-size: 56px; line-height: 1; margin-bottom: 12px;">✅</div>
        <span class="eyebrow" style="color: var(--green-primary);">${esc(t("success_eyebrow"))}</span>
        <h1 style="color: var(--green-primary);">${esc(t("success_title"))}</h1>
        <p class="subtitle" style="margin-top: 10px;">
          ${esc(t("success_subtitle"))}
        </p>

        <div class="panel" style="max-width: 520px; margin: 28px auto 0; text-align: left; background: #fff;">
          <h3 style="font-size: 18px; margin-bottom: 12px; color: var(--ink);">${esc(t("visit_details_title"))}</h3>
          <p style="font-size: 15px; margin-bottom: 6px;"><strong>${esc(t("patient_lbl"))}</strong> ${esc(state.patient?.name)} (${esc(t("patient_id_lbl"))} #${esc(state.patientId)})</p>
          <p style="font-size: 15px; margin-bottom: 6px;"><strong>${esc(t("consultation_record_lbl"))}</strong> #${esc(state.consultationId || "1")}</p>
          <p style="font-size: 15px; margin-bottom: 6px;"><strong>${esc(t("encounter_id_lbl"))}</strong> #${esc(state.encounterId)}</p>
          <p style="font-size: 15px;"><strong>${esc(t("status_lbl"))}</strong> <span class="status pending">${esc(t("pending_review_status"))}</span></p>
        </div>

        <div class="button-row" style="justify-content: center; margin-top: 32px;">
          <button class="primary-button" data-action="home" style="font-size: 16px;">${esc(t("finish_kiosk_btn"))}</button>
          <button class="outline-button" data-action="physician" style="font-size: 16px;">${esc(t("portal_btn"))} →</button>
        </div>
      </div>
    </section>
  `;
}

/* 11. PHYSICIAN REVIEW DASHBOARD */
function renderPhysicianDashboard() {
  const queue = state.queue || [];
  const counts = {
    pending: queue.filter(q => q.review_status === "pending").length,
    in_review: queue.filter(q => q.review_status === "in_review").length,
    verified: queue.filter(q => q.review_status === "verified").length,
    completed: queue.filter(q => q.review_status === "completed").length,
  };

  return `
    <section class="page">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 12px;">
        <div>
          <span class="eyebrow">PHYSICIAN CLINICAL WORKSPACE</span>
          <h1 style="font-size: 30px; margin: 4px 0 6px;">Outpatient Review Queue</h1>
          <p class="muted">Inspect source-backed patient records, verify findings, and complete consultations.</p>
        </div>
        <div class="button-row">
          <button class="outline-button" data-action="refresh-queue">🔄 Refresh Queue</button>
          <button class="quiet-button" data-action="home">Exit to Kiosk</button>
        </div>
      </div>

      <!-- METRIC COUNTERS -->
      <div class="four-grid">
        <div class="metric-card">
          <b>${counts.pending}</b>
          <small>Pending Reviews</small>
        </div>
        <div class="metric-card">
          <b style="color: var(--amber-primary);">${counts.in_review}</b>
          <small>In Review</small>
        </div>
        <div class="metric-card">
          <b style="color: var(--green-primary);">${counts.verified}</b>
          <small>Verified</small>
        </div>
        <div class="metric-card">
          <b style="color: #64748b;">${counts.completed}</b>
          <small>Completed</small>
        </div>
      </div>

      <!-- CONSULTATION QUEUE -->
      <div class="panel" style="margin-top: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
          <h2 style="font-size: 20px;">Consultation Records</h2>
          ${tagHtml("AUTOMATED DATA REMAINS UNVERIFIED UNTIL SIGNED", "automated")}
        </div>

        ${queue.length === 0 ? `
          <div class="choice-card" style="text-align: center; padding: 40px; background: #f8fafc;">
            <p class="muted">No consultation records in queue yet. When a patient completes a kiosk check-in, their record will appear here.</p>
          </div>
        ` : `
          <div style="display: grid; gap: 12px;">
            ${queue.map(item => `
              <div
                class="queue-card"
                style="cursor: pointer;"
                data-action="open-review-packet"
                data-patient-id="${item.patient_id}"
                data-encounter-id="${item.encounter_id}"
                data-consultation-id="${item.consultation_id}"
              >
                <div class="queue-card-head">
                  <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <strong style="font-size: 17px; color: var(--ink);">
                      👤 ${esc(item.patient_name)}
                    </strong>
                    ${item.priority === "urgent" ? `
                      <span class="tag urgent pulse-urgent" style="background: #fee2e2; color: #b91c1c; border: 1px solid #f87171; font-weight: 700; font-size: 11px;">
                        🚨 URGENT TRIAGE ${item.red_flag_reason ? `(${esc(item.red_flag_reason)})` : ""}
                      </span>
                    ` : item.priority === "priority" ? `
                      <span class="tag warning" style="background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; font-weight: 600; font-size: 11px;">
                        ⚠️ PRIORITY
                      </span>
                    ` : `
                      <span class="tag" style="background: #f1f5f9; color: #475569; font-size: 11px;">Routine</span>
                    `}
                  </div>
                  <span class="status ${esc(item.review_status)}">${esc(item.review_status.replace("_", " "))}</span>
                </div>
                <div style="font-size: 14px; color: var(--muted); margin-top: 4px;">
                  Patient #${esc(item.patient_id)} · Encounter #${esc(item.encounter_id)} · Consultation #${esc(item.consultation_id)}
                </div>
                <div style="font-size: 14px; margin-top: 6px; color: var(--ink-light);">
                  <strong>Chief Complaint:</strong> ${esc(item.chief_complaint || "None recorded")}
                </div>
              </div>
            `).join("")}
          </div>
        `}
      </div>
    </section>
  `;
}

/* 12. PHYSICIAN REVIEW PACKET */
function renderPhysicianReviewPacket() {
  const packet = state.packet;
  if (!packet) return renderPhysicianDashboard();

  const consultationId = state.activeReviewConsultationId;
  const currentConsultation = (packet.consultations || []).find(c => c.consultation_id === consultationId) || packet.consultations?.[0];
  const reviewStatus = currentConsultation?.review_status || "pending";
  const extractions = packet.medical_extraction || [];

  return `
    <section class="page">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
        <button class="outline-button" data-action="physician">← Back to Queue</button>
        <div class="button-row">
          <button
            class="outline-button"
            data-action="view-fhir-bundle"
            data-patient-id="${packet.patient?.patient_id}"
            data-encounter-id="${packet.encounter?.encounter_id || ""}"
            style="font-size: 13.5px; border-color: var(--teal-primary); color: var(--teal-dark); font-weight: 600;"
          >
            📋 View / Export FHIR R4 Bundle
          </button>
          <span class="status ${esc(reviewStatus)}" style="font-size: 13px; padding: 6px 14px;">
            Status: ${esc(reviewStatus.replace("_", " "))}
          </span>
        </div>
      </div>

      ${(packet.priority === "urgent" || currentConsultation?.priority === "urgent") ? `
        <div class="triage-urgent-banner">
          <div style="font-size: 28px;">🚨</div>
          <div>
            <strong style="color: #991b1b; font-size: 16px;">HIGH-SENSITIVITY RED FLAG DETECTED — URGENT TRIAGE ESCALATION</strong>
            <p style="margin-top: 4px; font-size: 14px; color: #7f1d1d;">
              Triage Reason: <strong>${esc(packet.red_flag_reason || currentConsultation?.red_flag_reason || "Urgent clinical trigger identified")}</strong>.
              This patient is prioritized at the top of the outpatient queue.
            </p>
          </div>
        </div>
      ` : ""}

      <div class="physician-layout">
        <!-- SIDEBAR: PATIENT DEMOGRAPHICS & NOTICE -->
        <aside>
          <div class="queue-panel">
            <span class="eyebrow">PATIENT PROFILE</span>
            <h2 style="font-size: 22px; margin: 8px 0 4px;">${esc(packet.patient?.name)}</h2>
            <p class="muted" style="font-size: 14px; margin-bottom: 14px;">
              Patient #${esc(packet.patient?.patient_id)} · Encounter #${esc(packet.encounter?.encounter_id || "None")}
            </p>

            <div style="font-size: 14px; display: grid; gap: 6px; margin-bottom: 18px;">
              <div><strong>Age:</strong> ${esc(packet.patient?.age)} yrs</div>
              <div><strong>Gender:</strong> ${esc(packet.patient?.gender)}</div>
              <div><strong>ABHA ID:</strong> ${esc(packet.patient?.abha_id || "Not linked")}</div>
              <div><strong>Consultation ID:</strong> #${esc(currentConsultation?.consultation_id || consultationId)}</div>
            </div>

            <div class="alert-box" style="background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; font-size: 13px;">
              <strong>Verification Notice:</strong>
              ${esc(packet.physician_verification_notice || "Automated information is not physician verified. Sign off required.")}
            </div>
          </div>
        </aside>

        <!-- MAIN REVIEW CONTENT & ACTION FORM -->
        <div style="display: grid; gap: 24px;">
          <!-- REVIEW CONTENT SECTIONS -->
          <div class="panel">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
              <div>
                <span class="eyebrow">CLINICAL DATA</span>
                <h2 style="font-size: 22px; margin-top: 4px;">Reported Symptoms &amp; History</h2>
              </div>
              ${tagHtml("UNVERIFIED SOURCE DATA", "automated")}
            </div>

            <p style="margin-bottom: 12px;"><strong>Chief Complaint:</strong> ${esc(packet.encounter?.chief_complaint || "Not recorded")}</p>
            
            <h4 style="font-size: 15px; margin-top: 14px; margin-bottom: 6px;">Reported Symptoms:</h4>
            ${(packet.symptoms || []).length > 0 ? `
              <ul style="margin: 0; padding-left: 20px; font-size: 14px;">
                ${packet.symptoms.map(s => `<li><strong>${esc(s.name)}:</strong> ${esc(s.description || s.duration || "Reported")}</li>`).join("")}
              </ul>
            ` : `<p class="muted" style="font-size: 14px;">No discrete symptoms reported.</p>`}

            <h4 style="font-size: 15px; margin-top: 14px; margin-bottom: 6px;">Medications &amp; Allergies:</h4>
            <div class="two-grid" style="margin-top: 8px;">
              <div style="background: #f8fafc; padding: 12px; border-radius: var(--radius-sm);">
                <strong>Medications:</strong>
                ${(packet.medications || []).length > 0 ? `
                  <ul style="margin: 4px 0 0; padding-left: 18px; font-size: 13.5px;">
                    ${packet.medications.map(m => `<li>${esc(m.name)} ${esc(m.dose || "")}</li>`).join("")}
                  </ul>
                ` : `<p class="muted" style="font-size: 13px; margin-top: 4px;">None</p>`}
              </div>

              <div style="background: #f8fafc; padding: 12px; border-radius: var(--radius-sm);">
                <strong>Allergies:</strong>
                ${(packet.allergies || []).length > 0 ? `
                  <ul style="margin: 4px 0 0; padding-left: 18px; font-size: 13.5px;">
                    ${packet.allergies.map(a => `<li>${esc(a.substance)} (${esc(a.reaction || "None")})</li>`).join("")}
                  </ul>
                ` : `<p class="muted" style="font-size: 13px; margin-top: 4px;">None reported</p>`}
              </div>
            </div>
          </div>

          <!-- AYUSH DUAL-CODING & DASHAVIDHA PARIKSHA -->
          <div class="ayush-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
              <div>
                <span class="eyebrow" style="color: #854d0e;">AYUSH DUAL-CODING &amp; TRADITIONAL MEDICINE MODULE 2</span>
                <h3 style="font-size: 20px; margin: 4px 0 2px; color: #713f12;">NAMASTE &amp; WHO ICD-11 Dual-Coding</h3>
                <p class="muted" style="font-size: 13px;">
                  Deterministic Local Catalog Lookup (Zero AI Hallucination) · NRCES India Interoperability
                </p>
              </div>
              <span class="ayush-badge ${(packet.ayush_coding?.coding_status === 'mapped') ? 'mapped' : 'unmapped'}">
                ${(packet.ayush_coding?.coding_status === 'mapped') ? '✓ AYUSH Mapped' : 'Unmapped Condition'}
              </span>
            </div>

            <!-- CODES TABLE -->
            <div style="margin-top: 14px; overflow-x: auto;">
              <table class="med-table" style="font-size: 13.5px;">
                <thead>
                  <tr>
                    <th>Clinical Concept / Term</th>
                    <th>System</th>
                    <th>NAMASTE Code (Ministry of AYUSH)</th>
                    <th>WHO ICD-11 TM2 Code (Chapter 26)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${(packet.ayush_coding?.codes && packet.ayush_coding.codes.length > 0) ? packet.ayush_coding.codes.map(c => `
                    <tr>
                      <td><strong>${esc(c.concept)}</strong><br><small class="muted">Matched: "${esc(c.matched_term)}"</small></td>
                      <td><span class="tag" style="background: #fef3c7; color: #92400e; font-size: 11px;">${esc(c.system)}</span></td>
                      <td>
                        ${c.namaste_code ? `<strong>${esc(c.namaste_code)}</strong><br><small class="muted">${esc(c.namaste_term)}</small>` : `<span class="muted">Unmapped in catalog</span>`}
                      </td>
                      <td>
                        ${c.who_icd11_code ? `<strong>${esc(c.who_icd11_code)}</strong><br><small class="muted">${esc(c.who_icd11_term)}</small>` : `<span class="muted">Unmapped in catalog</span>`}
                      </td>
                      <td>
                        <span class="ayush-badge ${c.coding_status === 'mapped' ? 'mapped' : 'unmapped'}">
                          ${esc(c.coding_status)}
                        </span>
                      </td>
                    </tr>
                  `).join("") : `
                    <tr>
                      <td colspan="5" style="text-align: center; color: var(--muted); padding: 16px;">
                        No AYUSH diagnostic keywords detected in current visit symptoms.
                      </td>
                    </tr>
                  `}
                </tbody>
              </table>
            </div>

            <!-- DASHAVIDHA PARIKSHA 10-POINT ASSESSMENT CONTEXT -->
            ${packet.ayush_coding?.dashavidha_pariksha_context ? `
              <details style="margin-top: 16px; border: 1px solid #e2d9c2; border-radius: var(--radius-sm); padding: 10px 14px; background: #fff;">
                <summary style="cursor: pointer; font-weight: 700; color: #713f12; font-size: 14px;">
                  🌿 Dashavidha Pariksha (10-Fold Clinical Examination Framework) Context
                </summary>
                <div class="pariksha-grid">
                  ${Object.entries(packet.ayush_coding.dashavidha_pariksha_context).map(([k, v]) => `
                    <div class="pariksha-item">
                      <strong>${esc(k.replace(/^[0-9]+_/, "").replace(/_/g, " "))}</strong>
                      <span>${esc(v || "Pending Vaidya examination")}</span>
                    </div>
                  `).join("")}
                </div>
              </details>
            ` : ""}

            <div style="margin-top: 12px; font-size: 12px; color: #854d0e; font-style: italic;">
              * Note: AYUSH dual codes are emitted deterministically from the controlled catalog and remain unverified until signed by the attending practitioner.
            </div>
          </div>

          <!-- DOCUMENT EXTRACTIONS -->
          <div class="panel">
            <h2 style="font-size: 20px; margin-bottom: 12px;">Attached Medical Documents (${(packet.documents || []).length})</h2>
            ${(packet.documents || []).map(d => `
              <div style="padding: 12px; border: 1px solid var(--line); border-radius: var(--radius-sm); margin-bottom: 8px; font-size: 14px;">
                📄 <strong>${esc(d.filename)}</strong> (Doc #${esc(d.document_id)}) — Status: <span class="tag verified">${esc(d.ocr_status)}</span>
              </div>
            `).join("")}

            ${extractions.length > 0 ? `
              <h4 style="font-size: 15px; margin-top: 16px; margin-bottom: 8px;">Extracted Observations:</h4>
              <table class="med-table">
                <thead>
                  <tr>
                    <th>Observation</th>
                    <th>Value</th>
                    <th>Reference</th>
                    <th>Physician Verified</th>
                  </tr>
                </thead>
                <tbody>
                  ${extractions.flatMap(ex => ex.observations || []).map(obs => `
                    <tr>
                      <td>${esc(obs.name)}</td>
                      <td><strong>${esc(obs.value)}</strong> ${esc(obs.unit || "")}</td>
                      <td>${esc(obs.reference_range || "—")}</td>
                      <td>
                        ${obs.physician_verified ? `<span class="tag verified">Verified ✓</span>` : `<span class="tag automated">Unverified</span>`}
                      </td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            ` : ""}
          </div>

          <!-- PHYSICIAN REVIEW ACTIONS -->
          <form id="physician-action-form" class="panel" style="border: 2px solid var(--teal-primary);">
            <span class="eyebrow">PHYSICIAN ACTIONS</span>
            <h2 style="font-size: 22px; margin: 4px 0 12px;">Clinical Sign-off &amp; Verification</h2>
            <p class="muted" style="font-size: 14px; margin-bottom: 16px;">
              Select the fields you have reviewed and verified against source records. Verification records an affirmative clinical sign-off in the hospital audit trail.
            </p>

            <label for="physician-id-input">
              Attending Physician ID / Badge
              <input id="physician-id-input" name="physician_id" type="text" maxlength="100" value="${esc(currentConsultation?.physician_id || "DR-DEFAULT-01")}" required>
            </label>

            <label for="physician-notes-input">
              Physician Clinical Notes
              <textarea id="physician-notes-input" name="notes" rows="3" placeholder="Enter clinical assessment notes here...">${esc(currentConsultation?.physician_notes || "")}</textarea>
            </label>

            <div style="margin-top: 18px;">
              <strong style="display: block; font-size: 14px; margin-bottom: 8px;">Verify Fields:</strong>
              <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                <label style="margin: 0; display: inline-flex; align-items: center; gap: 6px; font-weight: 500;">
                  <input type="checkbox" name="field-symptoms" checked style="width: 18px; height: 18px;"> Symptoms
                </label>
                <label style="margin: 0; display: inline-flex; align-items: center; gap: 6px; font-weight: 500;">
                  <input type="checkbox" name="field-medications" checked style="width: 18px; height: 18px;"> Medications
                </label>
                <label style="margin: 0; display: inline-flex; align-items: center; gap: 6px; font-weight: 500;">
                  <input type="checkbox" name="field-allergies" checked style="width: 18px; height: 18px;"> Allergies
                </label>
              </div>
            </div>

            <div id="physician-action-feedback" style="margin-top: 14px;"></div>

            <div class="button-row" style="margin-top: 24px;">
              <button type="button" class="outline-button" data-action="save-physician-notes">
                💾 Save Notes
              </button>
              <button type="button" class="primary-button" data-action="verify-physician-review">
                ✓ Verify Selected Fields
              </button>
              <button type="button" class="primary-button" style="background: var(--green-primary);" data-action="complete-physician-review">
                ✅ Complete Review &amp; Sign Off
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  `;
}

/* 13. ABHA & ABDM FLOW */
function renderAbdm() {
  const patientName = state.patient?.name || "Patient";
  const linkedAbha = state.patient?.abha_id;
  const isAbdmConsentActive = isConsentActive("abdm_sharing");

  return `
    <section class="page">
      <div class="panel">
        <span class="eyebrow">AYUSHMAN BHARAT DIGITAL MISSION (ABDM)</span>
        <h1 style="font-size: 28px; margin: 8px 0 6px;">ABHA Linking &amp; ABDM Sandbox Export</h1>
        <p class="muted">
          Patient: <strong>${esc(patientName)}</strong> (ID #${esc(state.patientId)}).
          Configure ABHA identification and prepare sandbox-ready exports. MediKiosk enforces independent consent before any export can be generated.
        </p>

        <div class="two-grid" style="margin-top: 24px;">
          <!-- ABHA LINKING -->
          <div class="panel" style="background: #f8fafc;">
            <h2 style="font-size: 20px; margin-bottom: 8px;">1. Link Local ABHA ID</h2>
            <p class="muted" style="font-size: 14px; margin-bottom: 14px;">
              Status: ${linkedAbha ? `<span class="tag verified">Linked: ${esc(linkedAbha)}</span>` : `<span class="tag urgent">Not Linked</span>`}
            </p>

            <form id="link-abha-form">
              <label for="abha-id-field">
                14-Digit ABHA Number / Address
                <input id="abha-id-field" name="abha_id" type="text" maxlength="32" value="${esc(linkedAbha || "")}" required placeholder="e.g. 12-3456-7890-1234">
              </label>

              <div class="button-row" style="margin-top: 16px;">
                <button type="submit" class="primary-button">
                  ${linkedAbha ? "Update Linked ABHA" : "Link ABHA ID"}
                </button>
              </div>
              <div id="abha-link-feedback" style="margin-top: 12px;"></div>
            </form>
          </div>

          <!-- ABDM CONSENT & EXPORT -->
          <div class="panel" style="background: #f8fafc;">
            <h2 style="font-size: 20px; margin-bottom: 8px;">2. ABDM Sharing Consent Gate</h2>
            <p class="muted" style="font-size: 14px; margin-bottom: 14px;">
              Status: ${isAbdmConsentActive ? `<span class="tag verified">Consent Active ✓</span>` : `<span class="tag urgent">Consent Required</span>`}
            </p>

            ${!isAbdmConsentActive ? `
              <div class="alert-box urgent-note" style="margin-bottom: 14px;">
                <strong>Consent Enforced:</strong> Export is strictly blocked until you explicitly grant ABDM sharing consent.
              </div>
              <button class="primary-button" data-action="grant-consent" data-purpose="abdm_sharing" style="width: 100%;">
                Grant ABDM Sharing Consent
              </button>
            ` : `
              <div class="alert-box" style="background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; margin-bottom: 14px;">
                ✓ Patient has granted permission to prepare sandbox-ready records.
              </div>
              <div class="button-row">
                <button class="primary-button" data-action="trigger-abdm-export" style="flex: 1;">
                  📤 Prepare Sandbox Export
                </button>
                <button class="outline-button" data-action="test-revoke-abdm" style="color: var(--red-primary); border-color: #fca5a5;">
                  Revoke Consent (Test Gate)
                </button>
              </div>
            `}
            <div id="abdm-export-feedback" style="margin-top: 14px;"></div>
          </div>
        </div>

        <div class="button-row" style="margin-top: 28px; justify-content: space-between;">
          <button class="outline-button" data-action="go-documents">← Back to Documents</button>
          <button class="primary-button" data-action="go-summary">Proceed to Summary →</button>
        </div>
      </div>
    </section>
  `;
}

/* =========================================================================
   MAIN RENDER DISPATCHER
   ========================================================================= */

function render() {
  updateLangButton();
  switch (state.screen) {
    case "welcome": appEl.innerHTML = renderWelcome(); break;
    case "language": appEl.innerHTML = renderLanguage(); break;
    case "identity": appEl.innerHTML = renderIdentity(); break;
    case "consent": appEl.innerHTML = renderConsent(); break;
    case "intake": appEl.innerHTML = renderIntake(); break;
    case "documents": appEl.innerHTML = renderDocuments(); break;
    case "structured": appEl.innerHTML = renderStructured(); break;
    case "summary": appEl.innerHTML = renderSummary(); break;
    case "review": appEl.innerHTML = renderReview(); break;
    case "success": appEl.innerHTML = renderSuccess(); break;
    case "physician": appEl.innerHTML = renderPhysicianDashboard(); break;
    case "physicianReview": appEl.innerHTML = renderPhysicianReviewPacket(); break;
    case "abdm": appEl.innerHTML = renderAbdm(); break;
    default: appEl.innerHTML = renderWelcome(); break;
  }
  bindEvents();
}

/* =========================================================================
   EVENT BINDINGS & ACTIONS
   ========================================================================= */

function bindEvents() {
  // Existing Patient Form
  const existingForm = document.querySelector("#existing-patient-form");
  if (existingForm) {
    existingForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const patientId = Number(document.querySelector("#existing-id-input").value);
      const out = document.querySelector("#existing-status-box");
      out.innerHTML = statusBadge("info", "Finding patient record…");
      try {
        const patient = await api(`/patients/${patientId}`);
        state.patient = patient;
        state.patientId = patient.id;
        if (patient.language) state.language = patient.language;
        await loadPatientConsents();
        setScreen("consent");
      } catch (err) {
        out.innerHTML = statusBadge("error", err.status === 404 ? "Patient ID not found. Please register as a new patient." : err.message);
      }
    });
  }

  // New Patient Form
  const newForm = document.querySelector("#new-patient-form");
  if (newForm) {
    newForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.querySelector("#reg-name-input").value.trim();
      const age = Number(document.querySelector("#reg-age-input").value);
      const gender = document.querySelector("#reg-gender-select").value;
      const phone = document.querySelector("#reg-phone-input").value.trim() || null;
      const abhaId = document.querySelector("#reg-abha-input").value.trim() || null;
      const out = document.querySelector("#new-status-box");
      
      out.innerHTML = statusBadge("info", "Registering new patient…");
      try {
        const patient = await api("/patients/", {
          method: "POST",
          body: JSON.stringify({
            name, age, gender, phone, abha_id: abhaId, language: state.language
          })
        });
        state.patient = patient;
        state.patientId = patient.id;
        state.consents = [];
        setScreen("consent");
      } catch (err) {
        out.innerHTML = statusBadge("error", err.message);
      }
    });
  }

  // Intake Chat Form
  const intakeForm = document.querySelector("#intake-chat-form");
  if (intakeForm) {
    intakeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.querySelector("#intake-message-input");
      const message = input ? input.value.trim() : "";
      if (!message) return;
      input.value = "";
      await submitIntakeMessage(message);
    });
  }

  // Document Upload Form
  const docForm = document.querySelector("#doc-upload-form");
  const fileInput = document.querySelector("#file-input");
  if (fileInput) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      const notice = document.querySelector("#file-chosen-notice");
      const nameEl = document.querySelector("#file-chosen-name");
      if (file && notice && nameEl) {
        nameEl.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        notice.style.display = "flex";
      }
    });
  }

  if (docForm) {
    docForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const file = fileInput?.files[0];
      const out = document.querySelector("#upload-feedback");
      if (!file) {
        if (out) out.innerHTML = statusBadge("error", "Please select a file first.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        if (out) out.innerHTML = statusBadge("error", "File exceeds the 10 MB limit.");
        return;
      }

      const formData = new FormData();
      formData.append("patient_id", state.patientId);
      if (state.encounterId) formData.append("encounter_id", state.encounterId);
      formData.append("file", file);

      if (out) out.innerHTML = statusBadge("info", "Uploading and validating document storage…");

      try {
        const doc = await api("/documents/upload", {
          method: "POST",
          body: formData,
          timeout: 45000,
        });
        state.documents.push(doc);
        state.activeDocumentId = doc.id;
        render();
      } catch (err) {
        if (out) out.innerHTML = statusBadge("error", err.message);
      }
    });
  }

  // ABHA Linking Form
  const abhaForm = document.querySelector("#link-abha-form");
  if (abhaForm) {
    abhaForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const abhaId = document.querySelector("#abha-id-field").value.trim();
      const out = document.querySelector("#abha-link-feedback");
      out.innerHTML = statusBadge("info", "Linking ABHA number locally…");
      try {
        const res = await api(`/patients/${state.patientId}/abha`, {
          method: "PUT",
          body: JSON.stringify({ abha_id: abhaId })
        });
        if (state.patient) state.patient.abha_id = res.abha_id;
        render();
        const feedback = document.querySelector("#abha-link-feedback");
        if (feedback) feedback.innerHTML = statusBadge("success", `ABHA ${res.abha_id} successfully linked locally.`);
      } catch (err) {
        out.innerHTML = statusBadge("error", err.message);
      }
    });
  }
}

/* GLOBAL CLICK DISPATCHER */
document.addEventListener("click", async (e) => {
  const target = e.target.closest("[data-action]");
  if (!target || target.disabled) return;

  const action = target.dataset.action;

  // Navigation
  if (action === "home") {
    setScreen("welcome");
  } else if (action === "start-touch") {
    setScreen("language");
  } else if (action === "start-voice") {
    setScreen("language");
  } else if (action === "go-language" || action === "language-menu") {
    setScreen("language");
  } else if (action === "select-lang") {
    state.language = target.dataset.code;
    render();
  } else if (action === "go-identity") {
    setScreen("identity");
  } else if (action === "go-consent") {
    await loadPatientConsents();
    setScreen("consent");
  } else if (action === "go-intake") {
    setScreen("intake");
  } else if (action === "go-documents") {
    setScreen("documents");
  } else if (action === "go-summary") {
    await loadClinicalSummary();
  } else if (action === "go-review") {
    setScreen("review");
  } else if (action === "go-abdm") {
    setScreen("abdm");
  }

  // Consent Actions
  else if (action === "grant-consent") {
    const purpose = target.dataset.purpose;
    try {
      await api(`/patients/${state.patientId}/consents`, {
        method: "POST",
        body: JSON.stringify({
          action: "grant",
          purpose,
          consent_version: "kiosk-v1",
          source: "kiosk_ui"
        })
      });
      await loadPatientConsents();
      render();
    } catch (err) {
      const fb = document.querySelector("#consent-feedback") || document.querySelector("#abdm-export-feedback");
      if (fb) fb.innerHTML = statusBadge("error", err.message);
    }
  } else if (action === "revoke-consent") {
    const consentId = Number(target.dataset.consentId);
    try {
      await api(`/patients/${state.patientId}/consents/${consentId}/revoke`, {
        method: "POST",
        body: JSON.stringify({ reason: "Patient revoked from kiosk" })
      });
      await loadPatientConsents();
      render();
    } catch (err) {
      const fb = document.querySelector("#consent-feedback");
      if (fb) fb.innerHTML = statusBadge("error", err.message);
    }
  } else if (action === "test-revoke-abdm") {
    const abdmConsent = getConsentRecord("abdm_sharing");
    if (abdmConsent) {
      try {
        await api(`/patients/${state.patientId}/consents/${abdmConsent.id}/revoke`, {
          method: "POST",
          body: JSON.stringify({ reason: "Testing ABDM gate revocation" })
        });
        await loadPatientConsents();
        render();
        const fb = document.querySelector("#abdm-export-feedback");
        if (fb) fb.innerHTML = statusBadge("warning", "ABDM consent revoked. Now attempt export to verify 403 Forbidden enforcement.");
      } catch (err) {
        alert(err.message);
      }
    }
  }

  // Start Intake Encounter
  else if (action === "start-intake-session") {
    if (!isConsentActive("clinical_history")) {
      const fb = document.querySelector("#consent-feedback");
      if (fb) fb.innerHTML = statusBadge("error", "Clinical History consent is required to start the intake session.");
      return;
    }
    const fb = document.querySelector("#consent-feedback");
    if (fb) fb.innerHTML = statusBadge("info", "Starting new intake encounter…");
    try {
      const res = await api("/intake/start", {
        method: "POST",
        body: JSON.stringify({
          patient_id: state.patientId,
          language: state.language,
          mode: "general"
        })
      });
      state.encounterId = res.encounter_id;
      state.intake = [{ role: "assistant", text: res.assistant_message }];
      state.redFlags = [];
      setScreen("intake");
    } catch (err) {
      if (fb) fb.innerHTML = statusBadge("error", err.message);
    }
  }

  // OCR Processing
  else if (action === "run-ocr") {
    const docId = Number(target.dataset.docId);
    target.disabled = true;
    target.textContent = "Analyzing Document (Nemotron OCR)…";
    try {
      const res = await api(`/documents/${docId}/ocr`, {
        method: "POST",
        timeout: 60000,
      });
      state.ocrResults[docId] = res;
      const d = state.documents.find(x => x.id === docId);
      if (d) d.ocr_status = "completed";
      render();
    } catch (err) {
      target.disabled = false;
      target.textContent = "🔍 Retry Nemotron OCR";
      const fb = document.querySelector("#upload-feedback");
      if (fb) fb.innerHTML = statusBadge("warning", `OCR could not complete: ${err.message}. The uploaded file is saved for manual physician review.`);
    }
  }

  // Medical Extraction
  else if (action === "run-extract") {
    const docId = Number(target.dataset.docId);
    state.activeDocumentId = docId;
    target.disabled = true;
    target.textContent = "Extracting Structured Data…";
    try {
      const extractRes = await api(`/documents/${docId}/extract`, {
        method: "POST",
        timeout: 45000,
      });
      state.extractions[docId] = extractRes;
      
      const intellRes = await api(`/documents/${docId}/intelligence`);
      state.intelligences[docId] = intellRes;
      setScreen("structured");
    } catch (err) {
      target.disabled = false;
      target.textContent = "⚡ View Structured Information →";
      const fb = document.querySelector("#upload-feedback");
      if (fb) fb.innerHTML = statusBadge("warning", safeProviderErrorMessage(err));
    }
  }

  // ABDM Export Trigger
  else if (action === "trigger-abdm-export") {
    const out = document.querySelector("#abdm-export-feedback");
    if (out) out.innerHTML = statusBadge("info", "Preparing sandbox export bundle…");
    try {
      const res = await api(`/patients/${state.patientId}/abdm/export`, {
        method: "POST",
        body: JSON.stringify({ encounter_id: state.encounterId })
      });
      if (out) {
        out.innerHTML = statusBadge("success", `Sandbox export prepared (${res.record_count} records). Provenance recorded; no production transmission made.`);
      }
    } catch (err) {
      if (out) {
        if (err.status === 403) {
          out.innerHTML = statusBadge("error", "403 Forbidden: Active ABDM sharing consent is strictly required.");
        } else if (err.status === 503) {
          out.innerHTML = statusBadge("warning", "ABDM sandbox credentials not configured on local server. Export request validated.");
        } else {
          out.innerHTML = statusBadge("error", err.message);
        }
      }
    }
  }

  // Submit Visit
  else if (action === "submit-final-visit") {
    const fb = document.querySelector("#submit-feedback");
    if (fb) fb.innerHTML = statusBadge("info", "Registering consultation with clinical queue…");
    try {
      const consultation = await api(`/patients/${state.patientId}/consultations`, {
        method: "POST",
        body: JSON.stringify({ encounter_id: state.encounterId })
      });
      state.consultationId = consultation.id;
      setScreen("success");
    } catch (err) {
      if (fb) fb.innerHTML = statusBadge("error", err.message);
    }
  }

  // Physician Review Portal Actions
  else if (action === "physician" || action === "refresh-queue") {
    try {
      const list = await api("/patients/physician/reviews");
      state.queue = list || [];
      setScreen("physician");
    } catch (err) {
      alert("Could not load physician queue: " + err.message);
    }
  } else if (action === "open-review-packet") {
    const pid = Number(target.dataset.patientId);
    const eid = Number(target.dataset.encounterId);
    const cid = Number(target.dataset.consultationId);
    state.activeReviewConsultationId = cid;

    try {
      const packet = await api(`/patients/${pid}/physician-review-packet?encounter_id=${eid}`);
      state.packet = packet;
      setScreen("physicianReview");
    } catch (err) {
      alert(err.status === 403 ? "Access Denied: Physician Review consent is not active for this patient." : err.message);
    }
  } else if (action === "save-physician-notes") {
    const form = document.querySelector("#physician-action-form");
    const physicianId = form.querySelector("[name=physician_id]").value.trim();
    const notes = form.querySelector("[name=notes]").value.trim();
    const out = document.querySelector("#physician-action-feedback");
    
    out.innerHTML = statusBadge("info", "Saving physician notes…");
    try {
      const res = await api(`/patients/${state.packet.patient.patient_id}/consultations/${state.activeReviewConsultationId}/review/notes`, {
        method: "POST",
        body: JSON.stringify({ physician_id: physicianId, notes })
      });
      // Refresh packet
      state.packet = await api(`/patients/${state.packet.patient.patient_id}/physician-review-packet?encounter_id=${state.packet.encounter.encounter_id}`);
      render();
      const fb = document.querySelector("#physician-action-feedback");
      if (fb) fb.innerHTML = statusBadge("success", "Clinical notes saved. Consultation status: in_review.");
    } catch (err) {
      out.innerHTML = statusBadge("error", err.message);
    }
  } else if (action === "verify-physician-review") {
    const form = document.querySelector("#physician-action-form");
    const physicianId = form.querySelector("[name=physician_id]").value.trim();
    const verifiedFields = [];
    if (form.querySelector("[name=field-symptoms]").checked) verifiedFields.push("symptoms");
    if (form.querySelector("[name=field-medications]").checked) verifiedFields.push("medications");
    if (form.querySelector("[name=field-allergies]").checked) verifiedFields.push("allergies");

    const out = document.querySelector("#physician-action-feedback");
    if (verifiedFields.length === 0) {
      out.innerHTML = statusBadge("error", "Please select at least one field to verify.");
      return;
    }

    out.innerHTML = statusBadge("info", "Recording affirmative physician verification…");
    try {
      await api(`/patients/${state.packet.patient.patient_id}/consultations/${state.activeReviewConsultationId}/review/verify`, {
        method: "POST",
        body: JSON.stringify({ physician_id: physicianId, verified_fields: verifiedFields })
      });
      state.packet = await api(`/patients/${state.packet.patient.patient_id}/physician-review-packet?encounter_id=${state.packet.encounter.encounter_id}`);
      render();
      const fb = document.querySelector("#physician-action-feedback");
      if (fb) fb.innerHTML = statusBadge("success", "Fields successfully verified. Consultation status: verified.");
    } catch (err) {
      out.innerHTML = statusBadge("error", err.message);
    }
  } else if (action === "complete-physician-review") {
    const form = document.querySelector("#physician-action-form");
    const physicianId = form.querySelector("[name=physician_id]").value.trim();
    const out = document.querySelector("#physician-action-feedback");
    out.innerHTML = statusBadge("info", "Signing off and completing consultation…");
    try {
      await api(`/patients/${state.packet.patient.patient_id}/consultations/${state.activeReviewConsultationId}/review/complete`, {
        method: "POST",
        body: JSON.stringify({ physician_id: physicianId })
      });
      state.packet = await api(`/patients/${state.packet.patient.patient_id}/physician-review-packet?encounter_id=${state.packet.encounter.encounter_id}`);
      render();
      const fb = document.querySelector("#physician-action-feedback");
      if (fb) fb.innerHTML = statusBadge("success", "Consultation completed and locked. Audit record created.");
    } catch (err) {
      out.innerHTML = statusBadge("error", err.status === 409 ? "Review must be verified before completing sign-off." : err.message);
    }
  }

  // Voice Recording & Confirmation Actions
  else if (action === "start-recording") {
    startMediaRecording();
  } else if (action === "stop-recording") {
    stopMediaRecording();
  } else if (action === "toggle-mic") {
    if (state.isRecording) stopMediaRecording();
    else startMediaRecording();
  } else if (action === "rerecord-voice") {
    state.pendingVoiceTranscript = "";
    render();
    startMediaRecording();
  } else if (action === "confirm-send-voice") {
    const el = document.querySelector("#voice-confirmed-text");
    const confirmedText = el ? el.value.trim() : state.pendingVoiceTranscript;
    state.pendingVoiceTranscript = "";
    submitIntakeMessage(confirmedText);
  }

  // Document Input & Camera Scanner Actions
  else if (action === "set-doc-mode") {
    const mode = target.dataset.mode || "file";
    state.docInputMode = mode;
    state.capturedDocBlob = null;
    state.capturedDocDataUrl = null;
    render();
    if (mode === "camera") {
      startDocCamera();
    } else {
      stopDocCamera();
    }
  } else if (action === "capture-camera-doc") {
    snapDocCamera();
  } else if (action === "retake-camera-doc") {
    state.capturedDocBlob = null;
    state.capturedDocDataUrl = null;
    render();
    startDocCamera();
  } else if (action === "confirm-upload-camera-doc") {
    if (state.capturedDocBlob) {
      uploadDocumentBlob(state.capturedDocBlob, `kiosk_camera_scan_${Date.now()}.jpg`);
    }
  }

  // FHIR R4 Bundle Modal Actions
  else if (action === "view-fhir-bundle") {
    const pid = target.dataset.patientId || state.patientId;
    const eid = target.dataset.encounterId || state.encounterId;
    const dialog = document.querySelector("#fhir-dialog");
    const viewer = document.querySelector("#fhir-json-display");
    const chips = document.querySelector("#fhir-resource-chips");

    if (viewer) viewer.textContent = "Generating NRCES India FHIR R4 Bundle from clinical database…";
    if (chips) chips.innerHTML = "";
    if (dialog) dialog.showModal();

    try {
      const url = eid ? `/patients/${pid}/fhir?encounter_id=${eid}` : `/patients/${pid}/fhir`;
      const bundle = await api(url);
      state.activeFhirBundle = bundle;

      const counts = {};
      (bundle.entry || []).forEach(e => {
        const rt = e.resource?.resourceType || "Resource";
        counts[rt] = (counts[rt] || 0) + 1;
      });

      if (chips) {
        chips.innerHTML = Object.entries(counts).map(([rt, cnt]) => `
          <span class="fhir-chip">${esc(rt)}: ${cnt}</span>
        `).join("") + `<span class="fhir-chip" style="background: #e0f2fe; color: #0369a1; border-color: #38bdf8;">Bundle total: ${bundle.total || (bundle.entry || []).length}</span>`;
      }

      if (viewer) {
        viewer.textContent = JSON.stringify(bundle, null, 2);
      }
    } catch (err) {
      if (viewer) viewer.textContent = "Failed to generate FHIR R4 Bundle: " + err.message;
    }
  } else if (action === "download-fhir-json") {
    if (!state.activeFhirBundle) return;
    const jsonStr = JSON.stringify(state.activeFhirBundle, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `medikiosk_fhir_r4_bundle_${state.activeFhirBundle.id || Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } else if (action === "copy-fhir-json") {
    if (!state.activeFhirBundle) return;
    const jsonStr = JSON.stringify(state.activeFhirBundle, null, 2);
    navigator.clipboard.writeText(jsonStr).then(() => {
      target.textContent = "✓ Copied!";
      setTimeout(() => { target.textContent = "📋 Copy to Clipboard"; }, 2000);
    }).catch(() => {
      alert("Could not copy to clipboard. Please select and copy manually.");
    });
  } else if (action === "close-fhir-dialog") {
    const dialog = document.querySelector("#fhir-dialog");
    if (dialog) dialog.close();
  }

  // Staff Call Modal
  else if (action === "nurse") {
    document.querySelector("#staff-dialog").showModal();
  } else if (action === "close-dialog") {
    document.querySelector("#staff-dialog").close();
  }
});

/* =========================================================================
   CAMERA DOCUMENT SCANNER HELPERS
   ========================================================================= */

async function startDocCamera() {
  stopDocCamera();
  const out = document.querySelector("#upload-feedback");
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (out) out.innerHTML = statusBadge("error", "Camera hardware is not accessible in this browser.");
    state.docInputMode = "file";
    render();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    state.cameraStream = stream;
    const videoEl = document.querySelector("#camera-video-stream");
    if (videoEl) {
      videoEl.srcObject = stream;
      await videoEl.play().catch(() => {});
    }
  } catch (err) {
    if (out) out.innerHTML = statusBadge("warning", `Camera access error: ${err.message}. Please use file upload.`);
    state.docInputMode = "file";
    render();
  }
}

function stopDocCamera() {
  if (state.cameraStream) {
    try {
      state.cameraStream.getTracks().forEach(t => t.stop());
    } catch (e) {}
    state.cameraStream = null;
  }
}

function snapDocCamera() {
  const videoEl = document.querySelector("#camera-video-stream");
  if (!videoEl) return;
  const canvas = document.createElement("canvas");
  canvas.width = videoEl.videoWidth || 1280;
  canvas.height = videoEl.videoHeight || 720;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

  stopDocCamera();
  canvas.toBlob((blob) => {
    state.capturedDocBlob = blob;
    state.capturedDocDataUrl = canvas.toDataURL("image/jpeg", 0.92);
    render();
  }, "image/jpeg", 0.92);
}

async function uploadDocumentBlob(blob, filename = "camera_document_scan.jpg") {
  const out = document.querySelector("#upload-feedback");
  if (out) out.innerHTML = statusBadge("info", "Uploading camera capture to secure hospital storage…");
  const formData = new FormData();
  formData.append("patient_id", state.patientId);
  if (state.encounterId) formData.append("encounter_id", state.encounterId);
  formData.append("file", blob, filename);

  try {
    const doc = await api("/documents/upload", {
      method: "POST",
      body: formData,
      timeout: 45000,
    });
    state.documents.push(doc);
    state.activeDocumentId = doc.id;
    state.capturedDocBlob = null;
    state.capturedDocDataUrl = null;
    state.docInputMode = "file";
    render();

    // Auto-run OCR on the uploaded image
    const docItem = state.documents.find(d => d.id === doc.id);
    if (docItem) {
      try {
        const ocrRes = await api(`/documents/${doc.id}/ocr`, { method: "POST", timeout: 60000 });
        state.ocrResults[doc.id] = ocrRes;
        docItem.ocr_status = "completed";
        render();
      } catch (ocrErr) {
        console.warn("Auto OCR background error:", ocrErr);
      }
    }
  } catch (err) {
    if (out) out.innerHTML = statusBadge("error", err.message);
  }
}

/* =========================================================================
   CLINICAL MESSAGE SUBMISSION (GROQ GPT OSS 120B)
   ========================================================================= */

async function submitIntakeMessage(message) {
  if (!message || !message.trim()) return;
  message = message.trim();

  state.intake.push({ role: "user", text: message });
  state.voicePreviewText = "";
  state.pendingVoiceTranscript = "";
  render();

  const out = document.querySelector("#intake-status-feedback");
  if (out) out.innerHTML = statusBadge("info", "Consulting Groq AI clinical assistant…");

  try {
    const res = await api("/intake/message", {
      method: "POST",
      body: JSON.stringify({ encounter_id: state.encounterId, message }),
      timeout: 40000,
    });
    state.intake.push({ role: "assistant", text: res.assistant_message });
    if (res.red_flags && res.red_flags.length > 0) {
      state.redFlags = res.red_flags;
    }
    if (res.status === "ready_for_review") {
      setScreen("documents");
    } else {
      render();
    }
  } catch (err) {
    const friendlyMsg = safeProviderErrorMessage(err);
    state.intake.push({
      role: "assistant",
      text: "Your response has been saved in this kiosk session. (Note: AI assistant response was delayed or unavailable)."
    });
    render();
    const feedback = document.querySelector("#intake-status-feedback");
    if (feedback) feedback.innerHTML = statusBadge("warning", friendlyMsg);
  }
}

/* =========================================================================
   VOICE RECORDING & GROQ WHISPER TRANSCRIPTION
   ========================================================================= */

let activeMediaRecorder = null;
let activeAudioChunks = [];
let activeRecordingTimer = null;

async function startMediaRecording() {
  if (state.isRecording) return;

  const out = document.querySelector("#intake-status-feedback");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (out) {
      out.innerHTML = statusBadge(
        "error",
        "Microphone recording is not supported in this browser. Please type your response."
      );
    }
    return;
  }

  try {
    if (out) out.innerHTML = statusBadge("info", "Requesting microphone permission from your browser…");
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    let mimeType = "audio/webm";
    if (window.MediaRecorder && typeof MediaRecorder.isTypeSupported === "function") {
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        mimeType = "audio/webm;codecs=opus";
      } else if (MediaRecorder.isTypeSupported("audio/webm")) {
        mimeType = "audio/webm";
      } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
        mimeType = "audio/mp4";
      } else if (MediaRecorder.isTypeSupported("audio/wav")) {
        mimeType = "audio/wav";
      }
    }

    activeMediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    activeAudioChunks = [];

    activeMediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        activeAudioChunks.push(event.data);
      }
    };

    activeMediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      clearInterval(activeRecordingTimer);
      state.isRecording = false;
      state.recordingSeconds = 0;

      if (activeAudioChunks.length === 0) {
        render();
        const feedback = document.querySelector("#intake-status-feedback");
        if (feedback) feedback.innerHTML = statusBadge("warning", "No audio captured. Please try speaking again.");
        return;
      }

      const blobType = activeMediaRecorder.mimeType || "audio/webm";
      const audioBlob = new Blob(activeAudioChunks, { type: blobType });
      const extension = blobType.includes("mp4") ? "mp4" : blobType.includes("wav") ? "wav" : "webm";
      const audioFile = new File([audioBlob], `patient_speech.${extension}`, { type: blobType });

      await transcribeAudioBlob(audioFile);
    };

    activeMediaRecorder.start(200);
    state.isRecording = true;
    state.recordingSeconds = 0;
    state.pendingVoiceTranscript = "";

    activeRecordingTimer = setInterval(() => {
      state.recordingSeconds = (state.recordingSeconds || 0) + 1;
      const timerEl = document.querySelector("#recording-timer");
      if (timerEl) {
        const mins = String(Math.floor(state.recordingSeconds / 60)).padStart(2, "0");
        const secs = String(state.recordingSeconds % 60).padStart(2, "0");
        timerEl.textContent = `${mins}:${secs}`;
      }
    }, 1000);

    render();
  } catch (err) {
    state.isRecording = false;
    render();
    const feedback = document.querySelector("#intake-status-feedback");
    if (feedback) {
      feedback.innerHTML = statusBadge(
        "error",
        "Microphone access was denied. Please allow microphone permissions in your browser URL address bar."
      );
    }
  }
}

function stopMediaRecording() {
  if (activeMediaRecorder && activeMediaRecorder.state !== "inactive") {
    activeMediaRecorder.stop();
  }
}

async function transcribeAudioBlob(audioFile) {
  state.isTranscribing = true;
  render();

  const formData = new FormData();
  formData.append("file", audioFile);
  if (state.language) {
    formData.append("language", state.language);
  }

  try {
    const res = await fetch(`${API_BASE}/intake/transcribe`, {
      method: "POST",
      body: formData,
    });

    state.isTranscribing = false;

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server returned ${res.status}`);
    }

    const data = await res.json();
    const transcript = (data.transcript || "").trim();

    if (!transcript) {
      state.pendingVoiceTranscript = "";
      render();
      const feedback = document.querySelector("#intake-status-feedback");
      if (feedback) {
        feedback.innerHTML = statusBadge("warning", "No audible speech was detected by Whisper. Please try speaking closer to the microphone.");
      }
      return;
    }

    state.pendingVoiceTranscript = transcript;
    render();
  } catch (err) {
    state.isTranscribing = false;
    render();
    const feedback = document.querySelector("#intake-status-feedback");
    if (feedback) {
      feedback.innerHTML = statusBadge("error", `Could not transcribe audio: ${err.message}. You may type your response below.`);
    }
  }
}

/* =========================================================================
   SUMMARY LOADER
   ========================================================================= */

async function loadClinicalSummary() {
  appEl.innerHTML = `
    <section class="page" style="text-align: center; padding-top: 100px;">
      <div class="spinner"></div>
      <h1 style="font-size: 26px;">Compiling Clinical Summary</h1>
      <p class="muted">Gathering verified patient history and source records…</p>
    </section>
  `;

  try {
    const summary = await api(`/patients/${state.patientId}/clinical-summary?encounter_id=${state.encounterId}`, {
      timeout: 30000,
    });
    state.summary = summary;
    state.summaryError = null;
  } catch (err) {
    state.summary = null;
    state.summaryError = safeProviderErrorMessage(err);
  }
  setScreen("summary");
}

/* =========================================================================
   INITIALIZATION
   ========================================================================= */

checkBackendHealth();
setInterval(checkBackendHealth, 15000);
render();
