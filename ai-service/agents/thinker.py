"""
agents/thinker.py — Think-Revise Loop (Phase 1.1)
Metacognitive critic pass that reviews initial council outputs and identifies
logical inconsistencies, missing differentials, and evidence gaps.
Inspired by OpenAI o1 extended thinking and Reflexion (Shinn et al., 2023).
"""

from typing import List, Dict, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# CRITIC SCORING RUBRIC
# ─────────────────────────────────────────────────────────────────────────────

CRITIC_GUIDE = """
You are a senior clinical reviewer evaluating a medical AI's differential diagnosis for logical consistency.

EVALUATION CRITERIA:
1. SYMPTOM-DIAGNOSIS ALIGNMENT: Does the top diagnosis explain ALL or MOST of the patient's symptoms?
2. PROBABILITY SANITY: Are probabilities differentiated and proportional to clinical likelihood?
3. MISSED DIFFERENTIALS: Is there a clinically important condition that was NOT included but should be?
4. EVIDENCE QUALITY: Is the evidence specific to THIS patient, or just generic symptom echoes?
5. URGENCY APPROPRIATENESS: Does the urgency level match the symptom severity and onset?

SCORING:
Rate each criterion 1–5. Score ≥ 4 on ALL criteria = acceptable. Any score ≤ 2 = must revise.
"""

# Conditions ALWAYS worth checking given symptom category
MUST_CHECK_MAP = {
    "headache":           ["Subarachnoid Hemorrhage", "Meningitis", "Hypertensive Emergency"],
    "chest pain":         ["Acute Myocardial Infarction", "Pulmonary Embolism", "Aortic Dissection"],
    "shortness of breath":["Pulmonary Embolism", "Pneumonia", "Severe Asthma"],
    "fever":              ["Sepsis", "Meningitis", "Endocarditis"],
    "abdominal pain":     ["Acute Appendicitis", "Bowel Perforation", "Ectopic Pregnancy"],
    "dizziness":          ["Cerebellar Stroke", "Vestibular Neuritis", "Cardiac Arrhythmia"],
    "seizure":            ["Encephalitis", "Hyponatraemia", "Brain Tumour"],
    "rash":               ["Meningococcal Septicaemia", "Anaphylaxis", "Stevens-Johnson Syndrome"],
}


def build_critic_prompt(soap_note: str, doctor_name: str, doctor_output: dict) -> str:
    """Build a meta-critic prompt that evaluates a single doctor's output."""
    top_3 = doctor_output.get("conditions", [])[:3]
    conditions_text = "\n".join(
        f"  {i+1}. {c.get('condition','?')} ({c.get('probability','?')}%) — "
        f"Evidence: {c.get('evidence',[])} — Reasoning: {c.get('reasoning','')[:120]}"
        for i, c in enumerate(top_3)
    )
    summary = doctor_output.get("reasoning_summary", "")

    return f"""{CRITIC_GUIDE}

PATIENT SOAP NOTE:
{soap_note}

{doctor_name}'s DIFFERENTIAL DIAGNOSIS:
{conditions_text}

Reasoning summary: {summary}

Evaluate this output. Respond JSON only:
{{
  "alignment_score": <1-5>,
  "probability_score": <1-5>,
  "evidence_score": <1-5>,
  "urgency_score": <1-5>,
  "needs_revision": <true_or_false>,
  "inconsistencies": ["<specific_error_1>", "<specific_error_2>"],
  "missing_differentials": ["<condition_that_should_be_included>"],
  "revision_instruction": "<one_sentence_specific_instruction_for_improvement>"
}}"""


def build_revision_prompt(soap_note: str, doctor: dict, original_output: dict, critique: dict) -> str:
    """Build a revision prompt that asks the doctor to correct their output based on the critique."""
    top_3 = original_output.get("conditions", [])[:3]
    original_text = "\n".join(
        f"  {i+1}. {c.get('condition','?')} ({c.get('probability','?')}%)"
        for i, c in enumerate(top_3)
    )
    instruction    = critique.get("revision_instruction", "Please improve your differential.")
    missing        = critique.get("missing_differentials", [])
    inconsistencies = critique.get("inconsistencies", [])

    missing_str = f"Consider adding: {', '.join(missing)}" if missing else ""
    issues_str  = "\n".join(f"  - {i}" for i in inconsistencies) if inconsistencies else "None identified"

    return f"""You are {doctor['name']}, {doctor['specialty']}.

You previously produced this differential:
{original_text}

A senior reviewer found these issues:
{issues_str}
{missing_str}

Reviewer instruction: {instruction}

Patient data:
{soap_note}

Revise your diagnosis to address the reviewer's concerns. Output corrected JSON only:
{{"doctor":"{doctor['name']}","specialty":"{doctor['specialty']}","conditions":[{{"condition":"<real_name>","probability":<integer>,"confidence":<integer>,"evidence":["<specific_finding>"],"reasoning":"<rationale>"}}],"missing_data":[],"urgent_flags":[],"reasoning_summary":"<revised_2_sentence_summary>"}}"""


def get_must_check_conditions(symptoms: List[str]) -> List[str]:
    """Return conditions that should always be considered for given symptoms."""
    must_check = []
    for symptom in symptoms:
        s_lower = symptom.lower()
        for key, conditions in MUST_CHECK_MAP.items():
            if key in s_lower:
                for c in conditions:
                    if c not in must_check:
                        must_check.append(c)
    return must_check


def parse_critique(critique_dict: dict) -> Tuple[bool, str]:
    """
    Returns (needs_revision, revision_instruction).
    Needs revision if any score <= 2 OR needs_revision flag is explicitly True.
    """
    needs_revision = bool(critique_dict.get("needs_revision", False))
    low_scores = [
        k for k in ["alignment_score", "probability_score", "evidence_score", "urgency_score"]
        if critique_dict.get(k, 5) <= 2
    ]
    if low_scores:
        needs_revision = True

    instruction = critique_dict.get("revision_instruction", "Improve the differential based on reviewer feedback.")
    return needs_revision, instruction
