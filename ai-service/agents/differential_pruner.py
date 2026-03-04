"""
agents/differential_pruner.py — Differential Diagnosis Pruner (Phase 1.3)
Eliminates conditions from the differential when key classic symptoms are absent.
Modeled on real internist diagnostic logic: "If it were X, the patient would have Y.
They don't have Y → X probability is reduced."
Used in Isabel DDx and VisualDx clinical decision support systems.
"""

from typing import List, Dict, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# CONDITION → REQUIRED SYMPTOM MAP
# "If the condition is present, you'd typically expect these symptoms"
# Absence of ≥N of these reduces the condition's probability
# ─────────────────────────────────────────────────────────────────────────────

CONDITION_REQUIREMENTS: Dict[str, Dict] = {
    "Bacterial Meningitis": {
        "classic_symptoms": {"neck stiffness", "fever", "headache", "photophobia", "altered consciousness"},
        "must_have_any":    {"neck stiffness", "meningism"},        # at least one of these is needed
        "penalty_each_absent": 15,                                   # % penalty per absent classic symptom
        "max_penalty": 40,
    },
    "Acute Myocardial Infarction": {
        "classic_symptoms": {"chest pain", "left arm pain", "sweating", "nausea", "jaw pain"},
        "must_have_any":    {"chest pain", "chest tightness"},
        "penalty_each_absent": 10,
        "max_penalty": 35,
    },
    "Pulmonary Embolism": {
        "classic_symptoms": {"shortness of breath", "chest pain", "leg swelling", "rapid breathing"},
        "must_have_any":    {"shortness of breath", "dyspnea"},
        "penalty_each_absent": 12,
        "max_penalty": 40,
    },
    "Acute Appendicitis": {
        "classic_symptoms": {"right lower quadrant pain", "abdominal pain", "nausea", "fever", "vomiting"},
        "must_have_any":    {"abdominal pain", "right side pain"},
        "penalty_each_absent": 10,
        "max_penalty": 35,
    },
    "Influenza": {
        "classic_symptoms": {"fever", "muscle aches", "fatigue", "headache", "cough"},
        "must_have_any":    {"fever"},
        "penalty_each_absent": 8,
        "max_penalty": 30,
    },
    "Aortic Dissection": {
        "classic_symptoms": {"severe chest pain", "tearing sensation", "back pain", "hypertension"},
        "must_have_any":    {"chest pain", "back pain"},
        "penalty_each_absent": 12,
        "max_penalty": 40,
    },
    "Stroke": {
        "classic_symptoms": {"facial droop", "arm weakness", "speech difficulty", "sudden onset", "dizziness"},
        "must_have_any":    {"weakness", "facial droop", "speech difficulty"},
        "penalty_each_absent": 10,
        "max_penalty": 35,
    },
    "Subarachnoid Hemorrhage": {
        "classic_symptoms": {"thunderclap headache", "severe headache", "photophobia", "neck stiffness", "vomiting"},
        "must_have_any":    {"severe headache", "headache"},
        "penalty_each_absent": 8,
        "max_penalty": 30,
    },
    "Anaphylaxis": {
        "classic_symptoms": {"rash", "hives", "throat swelling", "difficulty breathing", "exposure to allergen"},
        "must_have_any":    {"rash", "hives", "throat swelling"},
        "penalty_each_absent": 12,
        "max_penalty": 45,
    },
    "Gastroenteritis": {
        "classic_symptoms": {"nausea", "vomiting", "diarrhea", "abdominal cramping"},
        "must_have_any":    {"nausea", "vomiting", "diarrhea"},
        "penalty_each_absent": 8,
        "max_penalty": 30,
    },
    "Pneumonia": {
        "classic_symptoms": {"cough", "fever", "shortness of breath", "chest pain", "sputum"},
        "must_have_any":    {"cough", "fever"},
        "penalty_each_absent": 8,
        "max_penalty": 30,
    },
    "Urinary Tract Infection": {
        "classic_symptoms": {"burning urination", "frequency", "urgency", "pelvic pain"},
        "must_have_any":    {"burning urination", "urinary frequency", "dysuria"},
        "penalty_each_absent": 10,
        "max_penalty": 35,
    },
    "Asthma Exacerbation": {
        "classic_symptoms": {"wheeze", "shortness of breath", "cough", "chest tightness"},
        "must_have_any":    {"wheeze", "shortness of breath"},
        "penalty_each_absent": 10,
        "max_penalty": 35,
    },
    "Atrial Fibrillation": {
        "classic_symptoms": {"palpitations", "irregular heartbeat", "shortness of breath", "dizziness"},
        "must_have_any":    {"palpitations", "irregular heartbeat"},
        "penalty_each_absent": 10,
        "max_penalty": 30,
    },
}


def _symptom_present(symptom: str, patient_symptoms: List[str]) -> bool:
    """Check if a required symptom appears in the patient's symptoms (substring match)."""
    symptom_lo = symptom.lower()
    return any(symptom_lo in s.lower() or s.lower() in symptom_lo for s in patient_symptoms)


def prune_conditions(conditions: List[dict], patient_symptoms: List[str]) -> List[dict]:
    """
    Apply differential pruning based on absent classic symptoms.
    Reduces probability of conditions whose defining features are absent.
    Returns the modified conditions list.
    """
    if not conditions or not patient_symptoms:
        return conditions

    pruned = []
    for condition in conditions:
        name     = condition.get("condition", "")
        prob     = float(condition.get("probability", 50))
        conf     = float(condition.get("confidence", 50))
        evidence = list(condition.get("evidence", []))
        reasoning = condition.get("reasoning", "")

        # Find matching entry in requirements map (fuzzy)
        req_key = None
        name_lo = name.lower()
        for key in CONDITION_REQUIREMENTS:
            if key.lower() in name_lo or name_lo in key.lower():
                req_key = key
                break

        if req_key:
            req = CONDITION_REQUIREMENTS[req_key]
            classic = req["classic_symptoms"]
            must_have = req.get("must_have_any", set())
            penalty_each = req.get("penalty_each_absent", 10)
            max_penalty  = req.get("max_penalty", 35)

            # Check if at least one must-have symptom is present
            must_have_present = any(_symptom_present(s, patient_symptoms) for s in must_have)
            if not must_have_present and must_have:
                # Hard reduction — core symptom is missing
                total_penalty = min(max_penalty + 15, 55)
                new_prob = max(5, prob - total_penalty)
                new_conf = max(5, conf - 20)
                absent_must = list(must_have)[:2]
                reasoning   = f"[PRUNED] Missing core symptom(s): {', '.join(absent_must)}. " + reasoning
                evidence.append(f"ABSENT: {', '.join(absent_must)} — key discriminating feature not reported")
                print(f"[Pruner] ⬇️  {name}: {prob}% → {new_prob}% (missing core: {absent_must})")
                prob, conf = new_prob, new_conf

            else:
                # Soft reduction — count absent classic symptoms
                absent = [s for s in classic if not _symptom_present(s, patient_symptoms)]
                penalty = min(len(absent) * penalty_each, max_penalty)
                if penalty > 0:
                    new_prob = max(5, prob - penalty)
                    reasoning = f"[PRUNED -{penalty}%] {len(absent)} classic symptom(s) absent: {', '.join(list(absent)[:3])}. " + reasoning
                    print(f"[Pruner] ⬇️  {name}: {prob}% → {new_prob}% ({len(absent)} absent)")
                    prob = new_prob

        pruned.append({
            **condition,
            "probability": round(prob, 1),
            "confidence":  round(conf, 1),
            "evidence":    evidence,
            "reasoning":   reasoning,
        })

    # Re-sort by probability after pruning
    pruned.sort(key=lambda x: float(x.get("probability", 0)), reverse=True)
    return pruned


def get_pruning_summary(original: List[dict], pruned: List[dict]) -> str:
    """Return a human-readable summary of what pruning changed."""
    changes = []
    for orig, prun in zip(original, pruned):
        orig_prob = float(orig.get("probability", 0))
        prun_prob = float(prun.get("probability", 0))
        if abs(orig_prob - prun_prob) >= 5:
            changes.append(f"{orig.get('condition','?')}: {orig_prob}% → {prun_prob}%")
    return "; ".join(changes) if changes else "No pruning applied"
