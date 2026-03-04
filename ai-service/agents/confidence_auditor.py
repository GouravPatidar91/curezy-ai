"""
agents/confidence_auditor.py — Metacognitive Confidence Audit (Phase 1.4)
Final sanity-check LLM call after consensus. Computes an independent confidence
rating and produces "what would change my diagnosis" suggestions.
"""

from typing import Dict, List


AUDIT_PROMPT_TEMPLATE = """You are an independent senior clinician reviewing a differential diagnosis.

PATIENT DATA:
{soap_note}

PROPOSED DIFFERENTIAL:
{conditions_summary}

Current computed confidence: {confidence}%

Answer these questions concisely. JSON only:
{{
  "independent_confidence": <integer_5_to_95>,
  "confidence_rationale": "<one_sentence_why>",
  "what_would_change_diagnosis": ["<test_or_finding_1_that_would_change_the_top_diagnosis>", "<finding_2>"],
  "clinical_red_flags_missed": ["<any_emergency_missed>"],
  "audit_grade": "<A|B|C|D>"
}}

Grade A = top diagnosis is correct and differential complete.
Grade B = top diagnosis likely but differential incomplete.
Grade C = top diagnosis uncertain, key differentials missing.
Grade D = differential appears incorrect."""


def build_audit_prompt(soap_note: str, conditions: List[dict], confidence: float) -> str:
    conditions_summary = "\n".join(
        f"  {i+1}. {c.get('condition','?')} ({c.get('probability','?')}%) — {c.get('reasoning','')[:100]}"
        for i, c in enumerate(conditions[:3])
    )
    return AUDIT_PROMPT_TEMPLATE.format(
        soap_note=soap_note[:600],
        conditions_summary=conditions_summary,
        confidence=round(confidence, 1),
    )


def parse_audit_result(raw: dict, existing_missing: List[str]) -> Dict:
    """
    Parse and enrich the audit output.
    Returns enriched missing_data_suggestions and additional safety flags.
    """
    independent_conf      = raw.get("independent_confidence", None)
    change_triggers       = raw.get("what_would_change_diagnosis", [])
    red_flags_missed      = raw.get("clinical_red_flags_missed", [])
    audit_grade           = raw.get("audit_grade", "B")
    confidence_rationale  = raw.get("confidence_rationale", "")

    enriched_missing = list(existing_missing)
    for trigger in change_triggers:
        if trigger and len(str(trigger)) > 5:
            formatted = f"[Would clarify diagnosis] {trigger}"
            if formatted not in enriched_missing:
                enriched_missing.append(formatted)

    extra_flags = []
    for flag in red_flags_missed:
        if flag and len(str(flag)) > 5:
            extra_flags.append(f"[AUDIT FLAG] {flag}")
    if audit_grade == "D":
        extra_flags.append("[AUDIT] Differential may be incorrect — doctor review strongly advised")
    elif audit_grade == "C":
        extra_flags.append("[AUDIT] Differential incomplete — additional tests recommended")

    return {
        "independent_confidence": independent_conf,
        "audit_grade":            audit_grade,
        "confidence_rationale":   confidence_rationale,
        "enriched_missing":       enriched_missing,
        "extra_flags":            extra_flags,
    }


def confidence_adjustment(computed: float, audit_conf: float) -> float:
    """
    Blend the computed Bayesian confidence with the audit's independent confidence.
    If they differ by > 15%, flag the discrepancy and use a weighted average.
    """
    if audit_conf is None:
        return computed
    diff = abs(computed - audit_conf)
    if diff > 15:
        print(f"[Auditor] ⚠️  Large discrepancy: computed={computed}% vs audit={audit_conf}%")
    # 60% computed, 40% audit independent
    blended = (computed * 0.6) + (audit_conf * 0.4)
    return round(min(92.0, max(15.0, blended)), 1)
