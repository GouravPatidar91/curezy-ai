"""
agents/soap_converter.py — SOAP Note Converter (Phase 2.1)
Converts raw patient data into structured SOAP format before LLM analysis.
Used by MedPaLM 2 and GPT-4 Clinical to improve output specificity.
"""

from typing import List, Optional


def _safe_str(val) -> str:
    if isinstance(val, list):
        return ", ".join(str(v) for v in val if v)
    return str(val) if val else ""


def _classify_duration(duration_str: str) -> str:
    """Classify symptom duration into clinical categories."""
    if not duration_str or duration_str.lower() in ("unknown", ""):
        return "unknown"
    low = duration_str.lower()
    if any(w in low for w in ("hour", "hr", "minute", "min", "today", "just", "sudden")):
        return "acute (<24h)"
    if any(w in low for w in ("day", "yesterday", "2 days", "3 days", "48", "72")):
        return "acute (1-3 days)"
    if any(w in low for w in ("week", "4 day", "5 day", "6 day", "7 day")):
        return "subacute (1-2 weeks)"
    if any(w in low for w in ("month", "chronic", "long", "year", "ongoing")):
        return "chronic (>2 weeks)"
    return duration_str


def _classify_onset(duration_str: str, symptoms: List[str]) -> str:
    """Determine onset type from duration and symptom keywords."""
    low = (duration_str or "").lower()
    symptom_text = " ".join(symptoms).lower()
    if any(w in low or w in symptom_text for w in ("sudden", "abrupt", "instant", "worst ever")):
        return "SUDDEN (clinically significant)"
    if any(w in low for w in ("hour", "minute")):
        return "Acute"
    if "gradual" in low or "slowly" in low:
        return "Gradual"
    return "Unspecified"


def convert_to_soap(patient_state: dict) -> dict:
    """
    Convert structured patient_state to clinical SOAP note.
    Handles the new nested structure (patient_info, opqrst, etc.).
    """
    # ── 1. Extract Basic Info ──
    pi = patient_state.get("patient_info", {})
    age = pi.get("age") or patient_state.get("age", "unknown")
    gender = pi.get("gender") or patient_state.get("gender", "unknown")
    location = pi.get("location") or patient_state.get("location", "India")

    # ── 2. Extract Symptoms & OPQRST ──
    opqrst = patient_state.get("opqrst", {})
    chief_complaint = patient_state.get("chief_complaint") or ", ".join(patient_state.get("symptoms", []))
    
    onset = opqrst.get("onset") or patient_state.get("symptom_duration", "Not specified")
    provocation = opqrst.get("provocation") or "Not specified"
    quality = opqrst.get("quality") or "Not specified"
    region = opqrst.get("region") or "Not specified"
    severity = opqrst.get("severity") or "Not specified"
    timing = opqrst.get("timing") or "Not specified"

    # ── 3. Extract Histories ──
    def to_list(val):
        if not val: return []
        if isinstance(val, list): return val
        return [s.strip() for s in str(val).split(",") if s.strip()]

    associated = to_list(patient_state.get("associated_symptoms"))
    history = to_list(patient_state.get("medical_history")) or to_list(patient_state.get("medical_history_text"))
    meds = to_list(patient_state.get("medications")) or to_list(patient_state.get("medications_text"))
    allergies = to_list(patient_state.get("allergies"))
    family_history = to_list(patient_state.get("family_history"))
    
    lifestyle = patient_state.get("lifestyle", {})
    smoking = lifestyle.get("smoking") or "unknown"
    alcohol = lifestyle.get("alcohol") or "unknown"

    # ── 4. Build SOAP String ──────────────────────────────────────────────────
    
    # S (Subjective)
    subjective_lines = [
        f"Chief Complaint: {chief_complaint}",
        f"Onset: {onset}",
        f"Provocation/Palliation: {provocation}",
        f"Quality: {quality}",
        f"Region/Radiation: {region}",
        f"Severity: {severity}/10",
        f"Timing: {timing}",
        f"Associated Symptoms: {', '.join(associated) if associated else 'None'}"
    ]
    subjective = "\n".join(subjective_lines)

    # O (Objective)
    objective = f"Age: {age}, Gender: {gender}, Location: {location}"
    if patient_state.get("red_flag_detected"):
        objective += "\n⚠️ RED FLAG ALERT: Critical symptoms detected."

    # C (Context)
    context_lines = [
        f"Medical History: {', '.join(history) if history else 'None'}",
        f"Medications: {', '.join(meds) if meds else 'None'}",
        f"Allergies: {', '.join(allergies) if allergies else 'None'}",
        f"Lifestyle: Smoking: {smoking}, Alcohol: {alcohol}",
        f"Family History: {', '.join(family_history) if family_history else 'None'}"
    ]
    context = "\n".join(context_lines)

    soap_string = (
        f"S (Subjective):\n{subjective}\n\n"
        f"O (Objective):\n{objective}\n\n"
        f"C (Context):\n{context}"
    )

    return {
        "subjective": subjective,
        "objective": objective,
        "context": context,
        "soap_string": soap_string,
        "symptoms": [chief_complaint] + associated,
        "age": age,
        "gender": gender,
        "location": location,
        "red_flag_detected": patient_state.get("red_flag_detected", False)
    }
