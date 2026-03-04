"""
agents/counterfactual_reasoner.py — Counterfactual Reasoning Engine (Phase 4.1)
Answers: "What would the diagnosis be if X were different?"
Adds clinical insight about which symptoms are the most discriminating factors.
Inspired by Kaushik et al. (2020) counterfactual data augmentation.
"""

from typing import List, Dict, Tuple


COUNTERFACTUAL_PROMPT = """You are a clinical AI answering counterfactual questions about a medical case.

Original diagnosis: {condition} ({probability}%)
Patient: {soap_snippet}

Answer these 3 what-if questions. Be specific — name the condition that would change.
JSON only:

{{
  "age_counterfactual": {{
    "question": "Same symptoms but patient is {alt_age} years old instead of {age}",
    "diagnosis_change": "<same|different>",
    "new_top_condition": "<condition name or 'same'>",
    "clinical_reason": "<1 sentence>"
  }},
  "severity_counterfactual": {{
    "question": "If the most severe symptom were 2× worse",
    "diagnosis_change": "<same|different>",
    "new_top_condition": "<condition name or 'same'>",
    "new_conditions_added": ["<condition that would enter the differential>"],
    "clinical_reason": "<1 sentence>"
  }},
  "symptom_removal_counterfactual": {{
    "question": "Remove the most discriminating symptom: {key_symptom}",
    "diagnosis_change": "<same|different>",
    "new_top_condition": "<condition name if different>",
    "clinical_reason": "<1 sentence>",
    "insight": "<what this tells us about why {key_symptom} matters clinically>"
  }}
}}"""


def _pick_key_symptom(symptoms: List[str], top_condition: str) -> str:
    """Pick the most clinically discriminating symptom for the counterfactual."""
    # Simple heuristic: prefer symptoms that are less common
    DISCRIMINATING = [
        "neck stiffness", "meningism", "photophobia",     # Meningitis
        "left arm", "jaw pain", "radiation",               # ACS
        "thunderclap", "worst headache",                   # SAH
        "leg swelling", "recent travel",                   # PE
        "rebound tenderness", "right lower quadrant",      # Appendicitis
        "rash", "petechiae",                               # Meningococcemia
    ]
    for d in DISCRIMINATING:
        for s in symptoms:
            if d.lower() in s.lower():
                return s
    return symptoms[0] if symptoms else "fever"


def _alt_age(age) -> int:
    """Generate a contrasting age for the counterfactual."""
    try:
        age_int = int(age)
        if age_int < 40: return 70
        if age_int < 65: return 25
        return 30
    except:
        return 65


def build_counterfactual_prompt(top_condition: str, probability: float,
                                 soap: dict) -> str:
    """Build the counterfactual reasoning prompt."""
    key_symptom = _pick_key_symptom(soap.get("symptoms", []), top_condition)
    age         = soap.get("age", "unknown")
    alt_age_val = _alt_age(age)
    soap_snippet = soap.get("soap_string", "")[:350]

    return COUNTERFACTUAL_PROMPT.format(
        condition=top_condition,
        probability=round(probability, 1),
        soap_snippet=soap_snippet,
        age=age,
        alt_age=alt_age_val,
        key_symptom=key_symptom,
    )


def parse_counterfactual_output(raw: dict) -> List[str]:
    """
    Parse counterfactual output into user-facing insight strings.
    Returns a list of plain-language insight sentences.
    """
    insights = []

    for cf_key in ["age_counterfactual", "severity_counterfactual", "symptom_removal_counterfactual"]:
        cf = raw.get(cf_key, {})
        if not isinstance(cf, dict): continue

        reason  = str(cf.get("clinical_reason", "")).strip()
        insight = str(cf.get("insight", "")).strip()
        new_cond = str(cf.get("new_top_condition", "same")).strip()
        change   = str(cf.get("diagnosis_change", "same")).strip().lower()

        if change == "different" and new_cond and new_cond.lower() != "same":
            insights.append(f"If {cf.get('question','this factor changed')}: diagnosis shifts to {new_cond}. {reason}")
        elif insight:
            insights.append(insight)
        elif reason and len(reason) > 10:
            insights.append(reason)

    # Filter placeholder text
    return [i for i in insights if i and "<" not in i and len(i) > 15][:3]
