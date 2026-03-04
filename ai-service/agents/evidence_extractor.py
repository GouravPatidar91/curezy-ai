"""
agents/evidence_extractor.py — Clinical Evidence Extractor (Phase 2.4)
Dedicated LLM call that generates specific clinical evidence for a diagnosis,
replacing generic symptom echoes like ["fever", "headache"] with real clinical
findings like ["Acute onset fever 39°C", "Meningeal irritation consistent with photophobia"].
Pattern used in Microsoft BioGPT and Google MedPaLM 2.
"""

from typing import List, Optional


# Few-shot examples for evidence extraction quality
EVIDENCE_FEW_SHOT = """
=== EXAMPLE 1 ===
Patient: 28F, fever 39.5°C, neck stiffness, severe headache, photophobia, onset 6 hours
Diagnosis to support: Bacterial Meningitis

Clinical evidence:
1. Acute high fever (39.5°C) consistent with bacterial infection requiring LP
2. Neck stiffness (meningism) — positive meningeal irritation sign
3. Photophobia with severe headache — classic meningeal triad
4. Rapid 6-hour onset — typical bacterial time course (vs gradual viral)
5. Young adult (peak bacterial meningitis demographic)

=== EXAMPLE 2 ===
Patient: 45M, chest pain radiating to left arm, sweating, nausea, 30 minutes
Diagnosis to support: Acute Myocardial Infarction

Clinical evidence:
1. Substernal crushing chest pain with left arm radiation — STEMI equivalent
2. Diaphoresis (sweating) — sympathetic nervous system activation, ACS marker
3. 30-minute duration exceeds typical angina (<10 mins)
4. Male 45yo — high cardiac risk demographic (age + gender)
5. Associated nausea — vagal response consistent with inferior MI
"""


def build_evidence_prompt(diagnosis: str, soap_note: str) -> str:
    """Build a prompt that generates specific clinical evidence for a diagnosis."""
    return f"""You are a clinical evidence analyst. Your job is to identify SPECIFIC clinical evidence from the patient data that supports a given diagnosis.

RULES:
1. List exactly 4 specific evidence items
2. Each item must reference SPECIFIC patient data (numbers, timing, location)
3. Do NOT just list symptom names — explain WHY each finding supports the diagnosis
4. Format: JSON array of strings only

{EVIDENCE_FEW_SHOT}

=== YOUR TASK ===
Patient data:
{soap_note}

Diagnosis to support: {diagnosis}

List 4 specific clinical evidence items from this patient's data supporting {diagnosis}:
["<specific_finding_1>", "<specific_finding_2>", "<specific_finding_3>", "<specific_finding_4>"]

Respond with JSON array only:"""


def extract_evidence_from_raw(raw_output: str, fallback_symptoms: List[str]) -> List[str]:
    """Parse evidence from LLM output, fall back to cleaned symptoms if needed."""
    import json

    # Try to parse JSON array
    raw = raw_output.strip()
    if "[" in raw and "]" in raw:
        try:
            start = raw.find("[")
            end   = raw.rfind("]") + 1
            evidence_list = json.loads(raw[start:end])
            # Filter out short strings and placeholders
            cleaned = [
                str(e).strip() for e in evidence_list
                if isinstance(e, str) and len(str(e).strip()) > 10
                and "<" not in str(e) and ">" not in str(e)
                and str(e).lower() not in ("finding", "evidence", "placeholder")
            ]
            if cleaned:
                return cleaned[:4]
        except Exception:
            pass

    # Fallback: return formatted symptom strings
    return [f"Patient reported: {s}" for s in fallback_symptoms[:4]]
