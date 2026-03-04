"""
agents/fewshot_curator.py — Dynamic Few-Shot Example Curator (Phase 3.2)
Selects the most relevant case examples from the Case Library for each new patient,
replacing static worked examples with dynamically matched clinical cases.
"""

import os
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# STATIC FALLBACK FEW-SHOT EXAMPLES
# Used during cold start (< 50 cases in Case Library).
# ─────────────────────────────────────────────────────────────────────────────

STATIC_EXAMPLES: List[Dict] = [
    {
        "soap_note":  "S: fever 39.5°C, neck stiffness, severe headache, photophobia | Duration: acute (<24h) | Onset: SUDDEN\nO: Age 28, Female.\nC: PMH: none.",
        "condition":  "Bacterial Meningitis",
        "probability": 65,
        "evidence":   [
            "Acute onset fever 39.5°C — consistent with bacterial infection requiring LP",
            "Neck stiffness — positive meningeal irritation sign",
            "Photophobia with severe headache — classic meningeal triad",
            "6-hour rapid onset — bacterial time course vs. gradual viral"
        ],
        "reasoning":  "Classic bacterial meningitis triad with acute onset. LP + IV antibiotics within 1 hour.",
        "reasoning_summary": "Acute meningeal triad in young adult — bacterial meningitis primary diagnosis until LP excludes it.",
        "specialty":  "neurology",
        "urgency":    "EMERGENCY",
    },
    {
        "soap_note":  "S: chest pain radiating to left arm, sweating, nausea | Duration: 30 minutes | Onset: Acute\nO: Age 55, Male. Labs: none.\nC: PMH: hypertension. Meds: amlodipine.",
        "condition":  "Acute Myocardial Infarction",
        "probability": 72,
        "evidence":   [
            "Left arm radiation — classic ACS referred pain pattern",
            "Diaphoresis (sweating) — sympathetic activation, ACS marker",
            "Duration >30 min beyond typical angina threshold",
            "Male 55yo hypertensive — high Framingham cardiac risk"
        ],
        "reasoning":  "Classic STEMI/NSTEMI presentation. 12-lead ECG + cath lab activation immediate.",
        "reasoning_summary": "High-probability ACS in hypertensive male. Immediate ECG, cath lab, aspirin 300mg.",
        "specialty":  "cardiology",
        "urgency":    "EMERGENCY",
    },
]


def _symptom_overlap(case_symptoms: List[str], patient_symptoms: List[str]) -> float:
    """Compute Jaccard-style overlap between two symptom sets."""
    if not case_symptoms or not patient_symptoms:
        return 0.0
    case_set    = {s.lower().strip() for s in case_symptoms}
    patient_set = {s.lower().strip() for s in patient_symptoms}
    # Also check substring overlap
    matches = 0
    for ps in patient_set:
        for cs in case_set:
            if ps in cs or cs in ps:
                matches += 1
                break
    return matches / max(len(patient_set), 1)


def _format_case_as_example(case: Dict, doctor_name: str, doctor_specialty: str) -> str:
    """Format a case library entry as a few-shot example block."""
    evidence_str = "\n".join(f'"{e}"' for e in case.get("evidence", [])[:4])
    return f"""
=== WORKED EXAMPLE ({case.get('specialty','').upper()}) ===
Patient SOAP:
{case['soap_note']}

{doctor_name}'s clinical reasoning:
Step 1: Review chief complaint and onset type against differential candidates.
Step 2: Match key findings to the most clinically supported diagnosis.
Step 3: Assign probabilities based on specificity of findings.

{{"doctor":"{doctor_name}","specialty":"{doctor_specialty}","conditions":[{{"condition":"{case['condition']}","probability":{case['probability']},"confidence":75,"evidence":[{evidence_str}],"reasoning":"{case['reasoning']}"}}],"missing_data":[],"urgent_flags":["{case.get('urgency','routine')}: {case.get('reasoning_summary','')}"],"reasoning_summary":"{case.get('reasoning_summary','')}"}}\n"""


async def get_dynamic_examples(patient_symptoms: List[str], doctor: Dict, n: int = 2) -> str:
    """
    Fetch the most relevant few-shot examples for the current patient.
    Priority: Case Library (DB) → Static fallback.
    """
    try:
        # Try to fetch from Supabase case library
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            result = client.table("case_library").select(
                "soap_note, symptoms, top_condition, probability, evidence, reasoning, reasoning_summary, specialty, urgency"
            ).order("q_score", desc=True).limit(50).execute()

            if result.data:
                # Rank by symptom overlap with current patient
                scored = []
                for case in result.data:
                    overlap = _symptom_overlap(case.get("symptoms", []), patient_symptoms)
                    scored.append((overlap, case))
                scored.sort(key=lambda x: x[0], reverse=True)
                top_cases = [c for _, c in scored[:n]]

                if top_cases:
                    examples = ""
                    for case in top_cases:
                        examples += _format_case_as_example(
                            {
                                "soap_note":        case["soap_note"],
                                "condition":        case["top_condition"],
                                "probability":      case.get("probability", 60),
                                "evidence":         case.get("evidence", []),
                                "reasoning":        case.get("reasoning", ""),
                                "reasoning_summary": case.get("reasoning_summary", ""),
                                "specialty":        case.get("specialty", ""),
                                "urgency":          case.get("urgency", ""),
                            },
                            doctor["name"],
                            doctor["specialty"]
                        )
                    print(f"[FewShot] Dynamic examples: {len(top_cases)} from case library (top overlap: {scored[0][0]:.2f})")
                    return examples

    except Exception as e:
        print(f"[FewShot] DB fetch failed ({e}), using static fallback")

    # Fallback: rank static examples by symptom overlap
    scored_static = []
    for case in STATIC_EXAMPLES:
        case_syms = case["soap_note"].lower()
        match_count = sum(1 for s in patient_symptoms if s.lower() in case_syms)
        scored_static.append((match_count, case))
    scored_static.sort(key=lambda x: x[0], reverse=True)

    examples = ""
    for _, case in scored_static[:n]:
        examples += _format_case_as_example(case, doctor["name"], doctor["specialty"])

    print(f"[FewShot] Using {n} static fallback example(s)")
    return examples
