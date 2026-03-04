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
    Convert raw patient_state to structured SOAP note.
    Returns a dict with keys: subjective, objective, context, soap_string.
    """
    symptoms = [str(s) for s in patient_state.get("symptoms", [])]
    history  = [str(h) for h in patient_state.get("medical_history", [])]
    meds     = []
    for m in patient_state.get("medications", []):
        meds.append(m.get("name", str(m)) if isinstance(m, dict) else str(m))
    risks    = [str(r) for r in patient_state.get("risk_factors", [])]
    age      = patient_state.get("age", "unknown")
    gender   = patient_state.get("gender", "unknown")
    duration = patient_state.get("symptom_duration", "")

    # Build lab objective data
    lab_lines = []
    for lab in patient_state.get("lab_reports", []):
        if isinstance(lab, dict):
            flag = "⚠️ ABNORMAL" if lab.get("is_abnormal") else "normal"
            lab_lines.append(f"  • {lab.get('test_name', 'Unknown')}: {lab.get('value', 'N/A')} ({flag})")

    duration_class = _classify_duration(duration)
    onset_type     = _classify_onset(duration, symptoms)

    # ── Subjective (patient-reported) ────────────────────────────────────────
    subjective = (
        f"Chief complaint: {', '.join(symptoms) if symptoms else 'Not specified'}\n"
        f"Duration: {duration or 'Not specified'} [{duration_class}]\n"
        f"Onset: {onset_type}"
    )

    # ── Objective (clinical data) ─────────────────────────────────────────────
    objective_parts = [f"Age: {age}, Gender: {gender}"]
    if lab_lines:
        objective_parts.append("Laboratory results:\n" + "\n".join(lab_lines))
    else:
        objective_parts.append("Laboratory results: None provided")
    objective = "\n".join(objective_parts)

    # ── Context (PMH, Meds, RFs) ──────────────────────────────────────────────
    context = (
        f"Past Medical History (PMH): {', '.join(history) if history else 'No known conditions'}\n"
        f"Current Medications: {', '.join(meds) if meds else 'None'}\n"
        f"Risk Factors: {', '.join(risks) if risks else 'None identified'}"
    )

    # ── Full SOAP string for prompt injection ─────────────────────────────────
    soap_string = (
        f"S (Subjective — Patient Reported):\n{subjective}\n\n"
        f"O (Objective — Clinical Data):\n{objective}\n\n"
        f"C (Context — History & Risk):\n{context}"
    )

    return {
        "subjective":     subjective,
        "objective":      objective,
        "context":        context,
        "soap_string":    soap_string,
        "symptoms":       symptoms,
        "duration_class": duration_class,
        "onset_type":     onset_type,
        "age":            age,
        "gender":         gender,
        "has_labs":       bool(lab_lines),
    }
