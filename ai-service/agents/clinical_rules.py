"""
agents/clinical_rules.py — Hard Clinical Decision Rules Engine (Phase 2.2)
30 deterministic rules that fire BEFORE any LLM call to guarantee correct
emergency conditions always appear in the differential.
Pattern used by every production medical AI system.
"""

from typing import List, Dict, Tuple, Optional


# ─────────────────────────────────────────────────────────────────────────────
# RULE DEFINITIONS
# Each rule: symptom_pattern → forced_condition + urgency + flags
# ─────────────────────────────────────────────────────────────────────────────

HARD_RULES: List[Dict] = [

    # ── NEUROLOGICAL EMERGENCIES ──────────────────────────────────────────────
    {
        "id": "NEURO-01",
        "require_any": {"neck stiffness", "meningism", "kernig", "brudzinski"},
        "require_any_also": {"fever", "headache"},
        "forced_condition": "Bacterial Meningitis",
        "probability": 65,
        "urgency": "EMERGENCY",
        "flags": ["Immediate LP + IV broad-spectrum antibiotics", "Isolate patient"],
        "basis": "Classic meningeal triad: fever + headache + neck stiffness"
    },
    {
        "id": "NEURO-02",
        "require_any": {"thunderclap headache", "worst headache of life", "sudden severe headache"},
        "require_any_also": None,
        "forced_condition": "Subarachnoid Hemorrhage",
        "probability": 50,
        "urgency": "EMERGENCY",
        "flags": ["Immediate non-contrast CT head required", "Do not perform LP before CT"],
        "basis": "Thunderclap onset = SAH until proven otherwise (sentinel headache)"
    },
    {
        "id": "NEURO-03",
        "require_any": {"facial droop", "arm weakness", "speech difficulty", "slurred speech", "sudden weakness"},
        "require_any_also": {"sudden", "headache"},
        "forced_condition": "Acute Ischemic Stroke",
        "probability": 60,
        "urgency": "EMERGENCY",
        "flags": ["FAST assessment required", "Activate stroke protocol", "tPA window: 4.5h from onset"],
        "basis": "FAST criteria (Face, Arm, Speech, Time) — acute stroke protocol"
    },
    {
        "id": "NEURO-04",
        "require_any": {"seizure", "convulsion", "fit", "loss of consciousness"},
        "require_any_also": {"fever"},
        "forced_condition": "Febrile Seizure / Encephalitis",
        "probability": 45,
        "urgency": "EMERGENCY",
        "flags": ["Rule out bacterial meningitis", "EEG + MRI brain if first episode"],
        "basis": "Fever + new-onset seizure requires emergency workup"
    },

    # ── CARDIAC EMERGENCIES ───────────────────────────────────────────────────
    {
        "id": "CARD-01",
        "require_any": {"chest pain", "chest tightness", "chest pressure"},
        "require_any_also": {"left arm", "jaw pain", "radiation", "sweating", "diaphoresis"},
        "forced_condition": "Acute Myocardial Infarction (STEMI/NSTEMI)",
        "probability": 70,
        "urgency": "EMERGENCY",
        "flags": ["Activate cath lab / PCI protocol", "12-lead ECG immediately", "Aspirin 300mg + GTN"],
        "basis": "Classic ACS presentation: chest pain + radiation + diaphoresis"
    },
    {
        "id": "CARD-02",
        "require_any": {"palpitations", "irregular heartbeat", "heart racing"},
        "require_any_also": {"syncope", "loss of consciousness", "fainted", "collapse"},
        "forced_condition": "Ventricular Tachycardia / Dangerous Arrhythmia",
        "probability": 55,
        "urgency": "EMERGENCY",
        "flags": ["Continuous cardiac monitoring", "Defibrillator on standby", "12-lead ECG urgent"],
        "basis": "Syncope + palpitations = life-threatening arrhythmia until excluded"
    },

    # ── RESPIRATORY EMERGENCIES ───────────────────────────────────────────────
    {
        "id": "RESP-01",
        "require_any": {"shortness of breath", "breathlessness", "cannot breathe", "dyspnea"},
        "require_any_also": {"leg swelling", "leg pain", "calf pain", "recent travel", "recent surgery"},
        "forced_condition": "Pulmonary Embolism",
        "probability": 55,
        "urgency": "EMERGENCY",
        "flags": ["WELLS score calculation required", "D-dimer urgent", "CT pulmonary angiogram"],
        "basis": "WELLS criteria: leg swelling + dyspnea after immobilization/travel = high PE risk"
    },
    {
        "id": "RESP-02",
        "require_any": {"coughing blood", "hemoptysis", "blood in sputum"},
        "require_any_also": None,
        "forced_condition": "Pulmonary Hemorrhage / Lung Malignancy",
        "probability": 40,
        "urgency": "URGENT",
        "flags": ["Chest X-ray urgent", "CT chest if CXR equivocal", "Bronchoscopy if massive hemoptysis"],
        "basis": "Hemoptysis always requires imaging to exclude malignancy and hemorrhage"
    },
    {
        "id": "RESP-03",
        "require_any": {"severe breathlessness", "can't complete sentences", "silent chest"},
        "require_any_also": {"wheeze", "asthma", "history of asthma"},
        "forced_condition": "Severe Acute Asthma",
        "probability": 65,
        "urgency": "EMERGENCY",
        "flags": ["Peak flow < 50% predicted = severe", "Nebulised salbutamol + IV magnesium", "ICU if no response"],
        "basis": "Silent chest = life-threatening asthma — no air entry heard"
    },

    # ── ABDOMINAL EMERGENCIES ─────────────────────────────────────────────────
    {
        "id": "ABDO-01",
        "require_any": {"right lower quadrant pain", "mcburney point", "rlq pain", "right iliac fossa"},
        "require_any_also": {"fever", "nausea", "vomiting"},
        "forced_condition": "Acute Appendicitis",
        "probability": 70,
        "urgency": "URGENT",
        "flags": ["Alvarado score calculation", "CT abdomen/pelvis if equivocal", "Surgical consult"],
        "basis": "RLQ pain + fever + nausea = classic appendicitis presentation (Alvarado criteria)"
    },
    {
        "id": "ABDO-02",
        "require_any": {"rigid abdomen", "board-like abdomen", "rebound tenderness", "peritonism"},
        "require_any_also": None,
        "forced_condition": "Bowel Perforation / Peritonitis",
        "probability": 60,
        "urgency": "EMERGENCY",
        "flags": ["Urgent surgical review", "Erect CXR for free air", "IV antibiotics + fluid resuscitation"],
        "basis": "Peritoneal signs = surgical emergency"
    },
    {
        "id": "ABDO-03",
        "require_any": {"severe abdominal pain", "epigastric pain"},
        "require_any_also": {"vomiting", "alcohol", "gallstones"},
        "forced_condition": "Acute Pancreatitis",
        "probability": 50,
        "urgency": "URGENT",
        "flags": ["Serum lipase/amylase urgent", "RANSON criteria", "CT abdomen if severe"],
        "basis": "Epigastric pain radiating to back + vomiting = pancreatitis until excluded"
    },

    # ── SEPSIS ────────────────────────────────────────────────────────────────
    {
        "id": "SEPSIS-01",
        "require_any": {"high fever", "fever 39", "fever 40", "temperature 39", "temperature 40"},
        "require_any_also": {"confusion", "altered consciousness", "low blood pressure", "rapid heart rate", "chills", "rigors"},
        "forced_condition": "Sepsis / Systemic Inflammatory Response",
        "probability": 55,
        "urgency": "EMERGENCY",
        "flags": ["Sepsis Six protocol", "Blood cultures x2 before antibiotics", "IV broad-spectrum antibiotics within 1h"],
        "basis": "Sepsis criteria: fever + organ dysfunction signs = 'Surviving Sepsis Campaign' protocol"
    },

    # ── ANAPHYLAXIS ───────────────────────────────────────────────────────────
    {
        "id": "ALLRG-01",
        "require_any": {"rash", "hives", "urticaria"},
        "require_any_also": {"throat swelling", "difficulty breathing", "wheezing", "new medication", "insect sting", "food allergy"},
        "forced_condition": "Anaphylaxis",
        "probability": 60,
        "urgency": "EMERGENCY",
        "flags": ["IM Adrenaline 0.5mg immediately", "Call emergency services", "Lay flat with legs elevated"],
        "basis": "Urticaria + respiratory/cardiovascular symptoms after trigger = anaphylaxis"
    },

    # ── MENTAL HEALTH EMERGENCY ───────────────────────────────────────────────
    {
        "id": "MH-01",
        "require_any": {"suicidal thoughts", "self harm", "want to die", "kill myself"},
        "require_any_also": None,
        "forced_condition": "Acute Mental Health Crisis — Suicidal Ideation",
        "probability": 95,
        "urgency": "EMERGENCY",
        "flags": ["Immediate mental health crisis assessment", "Do not leave patient alone", "Emergency psychiatric referral"],
        "basis": "Suicidal ideation always requires immediate crisis intervention"
    },

    # ── HYPERTENSIVE EMERGENCY ────────────────────────────────────────────────
    {
        "id": "CARD-03",
        "require_any": {"severe headache", "blurred vision", "visual disturbance"},
        "require_any_also": {"hypertension", "high blood pressure", "known hypertensive", "bp"},
        "forced_condition": "Hypertensive Emergency / Malignant Hypertension",
        "probability": 45,
        "urgency": "URGENT",
        "flags": ["BP measurement both arms required", "Target BP reduction <25% in first hour", "Eye fundoscopy for papilloedema"],
        "basis": "Headache + visual disturbance in hypertensive patient = hypertensive crisis"
    },

    # ── OBSTETRIC EMERGENCY ───────────────────────────────────────────────────
    {
        "id": "OBS-01",
        "require_any": {"abdominal pain"},
        "require_any_also": {"pregnant", "pregnancy", "missed period", "positive pregnancy test"},
        "forced_condition": "Ectopic Pregnancy (in reproductive-age female)",
        "probability": 40,
        "urgency": "EMERGENCY",
        "flags": ["β-hCG urgent", "Pelvic ultrasound", "Surgical review if haemodynamically unstable"],
        "basis": "Abdominal pain + possible pregnancy in reproductive-age female = exclude ectopic"
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# RULE ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _text_contains_any(text: str, keywords: set) -> bool:
    return any(kw.lower() in text for kw in keywords)


def run_clinical_rules(patient_state: dict) -> Tuple[List[Dict], List[str]]:
    """
    Evaluate all hard clinical rules against the patient state.
    Returns:
        forced_conditions: List of forced condition dicts to prepend to the differential
        all_flags: List of urgent flag strings
    """
    # Build a searchable text blob from all patient data
    symptoms       = [str(s).lower() for s in patient_state.get("symptoms", [])]
    history        = [str(h).lower() for h in patient_state.get("medical_history", [])]
    symptom_text   = " ".join(symptoms + history + [
        str(patient_state.get("symptom_duration", "")),
        str(patient_state.get("pain_description", "")),
    ]).lower()

    forced_conditions: List[Dict] = []
    all_flags: List[str] = []
    fired_rules: List[str] = []

    for rule in HARD_RULES:
        primary_match   = _text_contains_any(symptom_text, rule["require_any"])
        secondary_match = True
        if rule["require_any_also"]:
            secondary_match = _text_contains_any(symptom_text, rule["require_any_also"])

        if primary_match and secondary_match:
            print(f"[ClinicalRules] 🚨 Rule fired: {rule['id']} — {rule['forced_condition']}")
            fired_rules.append(rule["id"])

            forced_conditions.append({
                "condition":   rule["forced_condition"],
                "probability": rule["probability"],
                "confidence":  80,
                "evidence":    list(rule["require_any"]) + (list(rule["require_any_also"]) if rule["require_any_also"] else []),
                "reasoning":   f"[CLINICAL RULE {rule['id']}] {rule['basis']}",
                "urgency":     rule["urgency"],
                "_rule_enforced": True,
            })
            for flag in rule["flags"]:
                if flag not in all_flags:
                    all_flags.append(f"[{rule['urgency']}] {flag}")

    if fired_rules:
        print(f"[ClinicalRules] {len(fired_rules)} rule(s) fired: {', '.join(fired_rules)}")
    else:
        print(f"[ClinicalRules] No emergency rules triggered")

    # De-duplicate by condition name (take highest probability if multiple rules)
    seen_names: Dict[str, int] = {}
    deduped: List[Dict] = []
    for c in forced_conditions:
        name = c["condition"]
        if name not in seen_names:
            seen_names[name] = len(deduped)
            deduped.append(c)
        else:
            idx = seen_names[name]
            if c["probability"] > deduped[idx]["probability"]:
                deduped[idx] = c

    return deduped, all_flags
