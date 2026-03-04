"""
agents/quality_scorer.py — Q-Score Quality Scorer (Phase 2.3)
Computes an objective Quality Score for each council output, independent of  
user feedback. Used as the primary training signal for Phase 3 auto-training.
"""

from typing import List, Dict


def _safe_float(val, default=0.0) -> float:
    try:    return float(val)
    except: return default


def _has_placeholder(text: str) -> bool:
    import re
    return bool(re.search(r"<[^>]{1,50}>", str(text))) or str(text).lower() in {
        "condition1", "finding", "rationale", "placeholder", "ev1"
    }


def score_agreement(agreement_score: float) -> float:
    """Score 0–100 based on council agreement. 3/3 → 100, 1/3 → 20."""
    return min(100, max(0, agreement_score * 100))


def score_confidence_validity(confidence: float) -> float:
    """
    Penalizes floor values (≤30%) and ceiling values (≥92%).
    An uncalibrated model often defaults to 60–65% for everything.
    """
    if 40 <= confidence <= 85:
        return 100.0  # Healthy range
    elif 30 <= confidence < 40:
        return 65.0   # Low but possible
    elif confidence < 30:
        return 30.0   # Suspiciously low — likely calibration error
    elif confidence > 88:
        return 70.0   # Suspiciously high — overconfidence
    return 80.0


def score_evidence_specificity(conditions: List[dict]) -> float:
    """
    Score 0–100 based on evidence quality.
    Penalizes:
    - Short evidence items (< 15 chars)
    - Placeholder evidence items
    - Evidence that just echoes symptom names
    Rewards:
    - Evidence with numbers, percentages, timing
    - Evidence with clinical context
    """
    if not conditions:
        return 0.0

    total_score = 0.0
    count = 0

    for cond in conditions[:3]:
        evidence = cond.get("evidence", [])
        if not evidence:
            total_score += 20.0
            count += 1
            continue

        ev_score = 0.0
        for ev in evidence[:4]:
            ev_str = str(ev).strip()
            if _has_placeholder(ev_str):
                ev_score += 0      # Placeholder = 0
            elif len(ev_str) < 10:
                ev_score += 10     # Too short = very low
            elif len(ev_str) < 20:
                ev_score += 35     # Short generic
            elif any(c.isdigit() for c in ev_str):
                ev_score += 90     # Contains numbers = specific
            elif any(w in ev_str.lower() for w in ("onset", "duration", "acute", "bilateral", "consistent", "absent")):
                ev_score += 80     # Contains clinical qualifiers
            else:
                ev_score += 55     # Generic but not placeholder

        cond_ev_score = ev_score / max(len(evidence[:4]), 1)
        total_score += cond_ev_score
        count += 1

    return round(total_score / max(count, 1), 1)


def score_probability_differentiation(conditions: List[dict]) -> float:
    """
    Score 0–100 based on how well-differentiated the probabilities are.
    All equal = 0 (template copy). Well spread = 100.
    """
    if len(conditions) < 2:
        return 50.0
    probs = [_safe_float(c.get("probability", 0)) for c in conditions]
    spread = max(probs) - min(probs)
    if spread <= 2:    return 0.0   # Flat / identical
    elif spread <= 10: return 35.0  # Slightly differentiated
    elif spread <= 25: return 70.0  # Good spread
    elif spread <= 50: return 90.0  # Excellent spread
    return 100.0


def score_rule_alignment(top_condition: str, forced_conditions: List[dict]) -> float:
    """
    Score 100 if the top condition matches what the clinical rules engine said (if rules fired).
    Score 50 if no rules fired (neutral).
    Score 0 if rules fired but LLM ignored them.
    """
    if not forced_conditions:
        return 50.0  # Neutral — no rules fired

    forced_names = {fc.get("condition", "").lower() for fc in forced_conditions}
    if top_condition.lower() in forced_names:
        return 100.0  # LLM agreed with rules
    return 0.0         # LLM disagreed with rules


def compute_q_score(
    council_output: dict,
    forced_conditions: List[dict] = None,
) -> Dict:
    """
    Compute the full Quality Score breakdown for a FinalClinicalOutput dict.
    Returns a dict with individual scores and overall Q-score (0–100).
    """
    conditions        = council_output.get("top_3_conditions", [])
    consensus_conf    = _safe_float(council_output.get("consensus_confidence", 0))
    agreement_score   = 1.0 if council_output.get("agents_agreed") else 0.5
    top_condition     = conditions[0].get("condition", "") if conditions else ""

    s_agreement  = score_agreement(agreement_score)
    s_confidence = score_confidence_validity(consensus_conf)
    s_evidence   = score_evidence_specificity(conditions)
    s_probs      = score_probability_differentiation(conditions)
    s_rules      = score_rule_alignment(top_condition, forced_conditions or [])

    q_score = (
        s_agreement  * 0.25 +
        s_confidence * 0.20 +
        s_evidence   * 0.25 +
        s_probs      * 0.20 +
        s_rules      * 0.10
    )

    return {
        "q_score":            round(q_score, 1),
        "agreement_score":    round(s_agreement, 1),
        "confidence_score":   round(s_confidence, 1),
        "evidence_score":     round(s_evidence, 1),
        "probability_score":  round(s_probs, 1),
        "rule_alignment":     round(s_rules, 1),
        "grade": (
            "A" if q_score >= 85 else
            "B" if q_score >= 70 else
            "C" if q_score >= 55 else
            "D"
        ),
    }
