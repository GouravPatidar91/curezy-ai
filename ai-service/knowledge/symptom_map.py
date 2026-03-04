"""
RAG-Lite Symptom → Differential Diagnosis Knowledge Base
Sources: NICE Clinical Guidelines, CDC Symptom Trees, BMJ Best Practice
Used to anchor LLM outputs to clinically relevant conditions
"""

from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# SYMPTOM CLUSTER → DIFFERENTIAL MAP
# Each entry: symptom_set → [(condition, urgency_level, typical_probability)]
# urgency: 'routine' | 'urgent' | 'emergency'
# ─────────────────────────────────────────────────────────────────────────────

SYMPTOM_DIFFERENTIAL_MAP: List[Dict] = [
    # ── Headache clusters ────────────────────────────────────────────────────
    {
        "symptoms":    {"headache", "fever", "neck stiffness", "photophobia"},
        "conditions":  [
            ("Bacterial Meningitis", "emergency", 65),
            ("Viral Meningitis", "urgent", 20),
            ("Encephalitis", "emergency", 10),
            ("Severe Influenza", "urgent", 5),
        ],
        "red_flags":   ["sudden onset", "rash", "altered consciousness"],
    },
    {
        "symptoms":    {"headache", "nausea", "vomiting", "photophobia"},
        "conditions":  [
            ("Migraine with Aura", "urgent", 50),
            ("Classical Migraine", "urgent", 30),
            ("Tension Headache", "routine", 10),
            ("Subarachnoid Hemorrhage", "emergency", 10),
        ],
        "red_flags":   ["thunderclap onset", "worst headache of life"],
    },
    {
        "symptoms":    {"headache", "fever", "nausea"},
        "conditions":  [
            ("Viral Upper Respiratory Infection", "routine", 40),
            ("Influenza", "urgent", 35),
            ("Sinusitis", "routine", 15),
            ("Migraine", "urgent", 10),
        ],
        "red_flags":   ["high fever > 39C", "stiff neck"],
    },
    {
        "symptoms":    {"headache", "dizziness", "blurred vision"},
        "conditions":  [
            ("Hypertensive Emergency", "emergency", 35),
            ("Vestibular Migraine", "urgent", 30),
            ("Transient Ischemic Attack", "emergency", 20),
            ("Benign Positional Vertigo", "routine", 15),
        ],
        "red_flags":   ["BP > 180/120", "sudden onset", "arm weakness"],
    },
    # ── Chest pain clusters ──────────────────────────────────────────────────
    {
        "symptoms":    {"chest pain", "shortness of breath", "sweating"},
        "conditions":  [
            ("Acute Myocardial Infarction", "emergency", 50),
            ("Unstable Angina", "emergency", 25),
            ("Pulmonary Embolism", "emergency", 15),
            ("Acute Pericarditis", "urgent", 10),
        ],
        "red_flags":   ["radiating to jaw/arm", "crushing pain", "diaphoresis"],
    },
    {
        "symptoms":    {"chest pain", "cough", "fever"},
        "conditions":  [
            ("Community-Acquired Pneumonia", "urgent", 45),
            ("Pleuritis", "urgent", 25),
            ("Bronchitis", "routine", 20),
            ("Costochondritis", "routine", 10),
        ],
        "red_flags":   ["hemoptysis", "high fever", "SpO2 < 94%"],
    },
    # ── Respiratory clusters ─────────────────────────────────────────────────
    {
        "symptoms":    {"shortness of breath", "wheezing", "cough"},
        "conditions":  [
            ("Asthma Exacerbation", "urgent", 45),
            ("COPD Exacerbation", "urgent", 30),
            ("Bronchitis", "routine", 15),
            ("Anaphylaxis", "emergency", 10),
        ],
        "red_flags":   ["silent chest", "cyanosis", "unable to speak"],
    },
    # ── Abdominal clusters ───────────────────────────────────────────────────
    {
        "symptoms":    {"abdominal pain", "fever", "nausea", "vomiting"},
        "conditions":  [
            ("Acute Appendicitis", "emergency", 35),
            ("Gastroenteritis", "routine", 30),
            ("Cholecystitis", "urgent", 20),
            ("Pancreatitis", "urgent", 15),
        ],
        "red_flags":   ["RLQ tenderness", "rebound tenderness", "rigidity"],
    },
    {
        "symptoms":    {"abdominal pain", "diarrhea", "nausea"},
        "conditions":  [
            ("Viral Gastroenteritis", "routine", 50),
            ("Food Poisoning", "routine", 30),
            ("Irritable Bowel Syndrome", "routine", 15),
            ("Inflammatory Bowel Disease", "urgent", 5),
        ],
        "red_flags":   ["bloody diarrhea", "high fever", "severe dehydration"],
    },
    # ── Fever clusters ───────────────────────────────────────────────────────
    {
        "symptoms":    {"fever", "fatigue", "sore throat", "swollen lymph nodes"},
        "conditions":  [
            ("Infectious Mononucleosis (EBV)", "urgent", 40),
            ("Bacterial Tonsillitis / Strep", "urgent", 35),
            ("Viral Pharyngitis", "routine", 20),
            ("Cytomegalovirus Infection", "routine", 5),
        ],
        "red_flags":   ["difficulty swallowing/breathing", "splenomegaly"],
    },
    {
        "symptoms":    {"fever", "chills", "muscle aches", "fatigue"},
        "conditions":  [
            ("Influenza", "urgent", 55),
            ("COVID-19", "urgent", 25),
            ("Malaria (if relevant travel)", "urgent", 10),
            ("Dengue Fever", "urgent", 10),
        ],
        "red_flags":   ["high fever > 40C", "rapid deterioration", "travel history"],
    },
    # ── Neurological clusters ────────────────────────────────────────────────
    {
        "symptoms":    {"dizziness", "nausea", "vomiting", "loss of balance"},
        "conditions":  [
            ("Benign Paroxysmal Positional Vertigo", "routine", 40),
            ("Acute Vestibular Neuritis", "urgent", 30),
            ("Ménière's Disease", "routine", 15),
            ("Cerebellar Stroke", "emergency", 15),
        ],
        "red_flags":   ["diplopia", "dysarthria", "falls", "sudden onset"],
    },
    # ── Skin clusters ────────────────────────────────────────────────────────
    {
        "symptoms":    {"rash", "fever", "joint pain"},
        "conditions":  [
            ("Viral Exanthem", "routine", 35),
            ("Systemic Lupus Erythematosus", "urgent", 25),
            ("Rheumatoid Arthritis (early)", "urgent", 20),
            ("Lyme Disease", "urgent", 20),
        ],
        "red_flags":   ["petechiae", "purpuric rash", "joint swelling"],
    },
    # ── Urinary clusters ─────────────────────────────────────────────────────
    {
        "symptoms":    {"burning urination", "frequency", "pelvic pain"},
        "conditions":  [
            ("Urinary Tract Infection", "routine", 60),
            ("Cystitis", "routine", 25),
            ("Pyelonephritis", "urgent", 10),
            ("Urethritis", "routine", 5),
        ],
        "red_flags":   ["flank pain", "high fever", "rigors"],
    },
    # ── Cardiac clusters ─────────────────────────────────────────────────────
    {
        "symptoms":    {"palpitations", "shortness of breath", "dizziness"},
        "conditions":  [
            ("Atrial Fibrillation", "urgent", 35),
            ("Supraventricular Tachycardia", "urgent", 30),
            ("Panic Disorder", "routine", 20),
            ("Ventricular Tachycardia", "emergency", 15),
        ],
        "red_flags":   ["syncope", "chest pain", "irregular pulse"],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# LOOKUP FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    return text.lower().strip()


def get_candidate_conditions(patient_symptoms: List[str]) -> List[Tuple[str, int]]:
    """
    Given a list of patient symptoms, return the top ranked differential
    conditions from the knowledge base using symptom cluster matching.
    Returns: list of (condition_name, estimated_probability) tuples, up to 6.
    """
    if not patient_symptoms:
        return []

    symptom_set = {_normalise(s) for s in patient_symptoms}
    scored: Dict[str, int] = {}
    voted_probs: Dict[str, List[int]] = {}

    for entry in SYMPTOM_DIFFERENTIAL_MAP:
        cluster = {_normalise(s) for s in entry["symptoms"]}
        # Count how many cluster symptoms match the patient
        overlap = len(symptom_set & cluster)
        if overlap == 0:
            continue

        match_ratio = overlap / len(cluster)
        if match_ratio < 0.3:  # Need at least 30% cluster match
            continue

        for condition, _, base_prob in entry["conditions"]:
            weighted = int(base_prob * match_ratio)
            scored[condition] = scored.get(condition, 0) + weighted
            voted_probs.setdefault(condition, []).append(int(base_prob * match_ratio))

    if not scored:
        return []

    # Sort by total weighted score descending
    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    return [(name, min(90, score)) for name, score in ranked[:6]]


def get_red_flags(patient_symptoms: List[str]) -> List[str]:
    """Return red flag indicators relevant to the patient's symptoms."""
    symptom_set = {_normalise(s) for s in patient_symptoms}
    flags = []
    for entry in SYMPTOM_DIFFERENTIAL_MAP:
        cluster = {_normalise(s) for s in entry["symptoms"]}
        if len(symptom_set & cluster) >= 2:
            for flag in entry.get("red_flags", []):
                if flag not in flags:
                    flags.append(flag)
    return flags[:5]


def format_rag_block(patient_symptoms: List[str]) -> str:
    """
    Returns a formatted string to inject into the LLM prompt,
    containing clinically-grounded candidate conditions.
    """
    candidates = get_candidate_conditions(patient_symptoms)
    if not candidates:
        return ""

    lines = ["CLINICALLY GROUNDED REFERENCE CONDITIONS (based on symptom cluster matching):"]
    for i, (condition, prob) in enumerate(candidates, 1):
        lines.append(f"  {i}. {condition} (~{prob}% base likelihood from literature)")
    lines.append("Your diagnosis MUST consider these conditions but is NOT limited to them.")
    lines.append("If you deviate from these, provide specific evidence for why.")
    return "\n".join(lines)
