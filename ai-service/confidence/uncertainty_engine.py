from typing import List, Optional
from pydantic import BaseModel


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class ConfidenceReport(BaseModel):
    overall_confidence: float
    confidence_level: str  # HIGH, MEDIUM, LOW, CRITICAL_LOW
    decay_factors: List[str]
    improvement_suggestions: List[str]
    is_reliable: bool
    uncertainty_warning: Optional[str]


# ─────────────────────────────────────────
# UNCERTAINTY ENGINE
# ─────────────────────────────────────────

class UncertaintyEngine:

    def __init__(self):
        self.high_threshold = 70.0
        self.medium_threshold = 50.0
        self.low_threshold = 30.0

    def _get_confidence_level(self, score: float) -> str:
        if score >= self.high_threshold:
            return "HIGH"
        elif score >= self.medium_threshold:
            return "MEDIUM"
        elif score >= self.low_threshold:
            return "LOW"
        else:
            return "CRITICAL_LOW"

    def analyze_clinical_confidence(
        self,
        patient_state: dict,
        clinical_analysis: dict
    ) -> ConfidenceReport:

        base_confidence = clinical_analysis.get("consensus_confidence", 0)
        decay_factors = []
        improvement_suggestions = []
        penalty = 0

        # Factor 1 — Data completeness
        completeness = patient_state.get("data_completeness_score", 0)
        if completeness < 50:
            penalty += 20
            decay_factors.append("Insufficient patient data")
            improvement_suggestions.append(
                "Collect complete symptom history and lab reports"
            )
        elif completeness < 75:
            penalty += 10
            decay_factors.append("Partial patient data")
            improvement_suggestions.append(
                "Additional lab reports would improve confidence"
            )

        # Factor 2 — Lab reports missing
        lab_reports = patient_state.get("lab_reports", [])
        if not lab_reports:
            penalty += 15
            decay_factors.append("No lab reports available")
            improvement_suggestions.append(
                "CBC, CRP, and basic metabolic panel recommended"
            )

        # Factor 3 — Agent disagreement
        agents_agreed = clinical_analysis.get("agents_agreed", True)
        if not agents_agreed:
            penalty += 20
            decay_factors.append("AI agents disagreed on diagnosis")
            improvement_suggestions.append(
                "Clinical correlation strongly recommended"
            )

        # Factor 4 — Abnormal labs present
        abnormal_labs = [
            lab for lab in lab_reports
            if lab.get("is_abnormal")
        ]
        if abnormal_labs:
            improvement_suggestions.append(
                f"Follow up on {len(abnormal_labs)} abnormal lab value(s)"
            )

        # Factor 5 — Missing imaging
        imaging = patient_state.get("imaging_findings")
        if not imaging:
            penalty += 5
            improvement_suggestions.append(
                "Chest X-ray or imaging would improve diagnostic confidence"
            )

        # Factor 6 — Risk factors present
        risk_factors = patient_state.get("risk_factors", [])
        if risk_factors:
            decay_factors.append(
                f"Patient has {len(risk_factors)} risk factor(s)"
            )

        # Calculate final confidence
        final_confidence = max(0, base_confidence - penalty)
        confidence_level = self._get_confidence_level(final_confidence)

        # Uncertainty warning
        warning = None
        if confidence_level == "CRITICAL_LOW":
            warning = "CRITICAL: Confidence too low for reliable assessment. Immediate doctor review required."
        elif confidence_level == "LOW":
            warning = "LOW CONFIDENCE: Results should be verified by a clinician before any action."

        return ConfidenceReport(
            overall_confidence=round(final_confidence, 1),
            confidence_level=confidence_level,
            decay_factors=decay_factors,
            improvement_suggestions=improvement_suggestions,
            is_reliable=final_confidence >= self.medium_threshold,
            uncertainty_warning=warning
        )

    def analyze_imaging_confidence(
        self,
        imaging_result: dict
    ) -> ConfidenceReport:

        quality = imaging_result.get("quality_assessment", {})
        findings = imaging_result.get("findings", [])
        decay_factors = []
        improvement_suggestions = []
        penalty = 0

        # Factor 1 — Image quality
        quality_score = quality.get("quality_score", 0)
        if quality_score < 50:
            penalty += 30
            decay_factors.append("Poor image quality")
            improvement_suggestions.append(
                "Retake X-ray with better positioning and exposure"
            )
        elif quality_score < 75:
            penalty += 15
            decay_factors.append("Suboptimal image quality")
            improvement_suggestions.append(
                "Better image quality would improve detection accuracy"
            )

        # Factor 2 — Quality issues
        issues = quality.get("issues", [])
        for issue in issues:
            decay_factors.append(f"Image issue: {issue}")

        # Factor 3 — Low primary confidence
        primary_confidence = (
            findings[0].get("confidence", 0) if findings else 0
        )
        if primary_confidence < 30:
            penalty += 20
            decay_factors.append("Low detection confidence")
            improvement_suggestions.append(
                "CT scan recommended for better visualization"
            )

        # Factor 4 — Close probabilities between findings
        if len(findings) >= 2:
            diff = abs(
                findings[0].get("probability", 0) -
                findings[1].get("probability", 0)
            )
            if diff < 10:
                penalty += 10
                decay_factors.append(
                    "Multiple conditions have similar probabilities"
                )
                improvement_suggestions.append(
                    "Additional clinical correlation needed"
                )

        final_confidence = max(0, primary_confidence - penalty)
        confidence_level = self._get_confidence_level(final_confidence)

        warning = None
        if confidence_level == "CRITICAL_LOW":
            warning = "CRITICAL: Image analysis confidence too low. Radiologist review mandatory."
        elif confidence_level == "LOW":
            warning = "LOW CONFIDENCE: Imaging findings should be verified by radiologist."

        return ConfidenceReport(
            overall_confidence=round(final_confidence, 1),
            confidence_level=confidence_level,
            decay_factors=decay_factors,
            improvement_suggestions=improvement_suggestions,
            is_reliable=final_confidence >= self.medium_threshold,
            uncertainty_warning=warning
        )

    def generate_active_data_gaps(
        self,
        patient_state: dict,
        clinical_analysis: dict
    ) -> List[str]:
        gaps = []

        # Check what's missing
        if not patient_state.get("lab_reports"):
            gaps.append(
                "CBC (Complete Blood Count) — could improve confidence by ~25%"
            )
            gaps.append(
                "CRP test — would help differentiate bacterial vs viral infection"
            )

        if not patient_state.get("imaging_findings"):
            gaps.append(
                "Chest X-ray — would improve respiratory condition confidence by ~30%"
            )

        if not patient_state.get("age"):
            gaps.append("Patient age — affects risk stratification significantly")

        if not patient_state.get("symptom_duration"):
            gaps.append(
                "Symptom duration — helps differentiate acute vs chronic conditions"
            )

        conditions = clinical_analysis.get("top_3_conditions", [])
        if conditions:
            top = conditions[0]
            condition_name = (
                top.get("condition", "") if isinstance(top, dict)
                else getattr(top, "condition", "")
            )
            if "pneumonia" in condition_name.lower():
                gaps.append(
                    "Sputum culture — would confirm bacterial pneumonia diagnosis"
                )
            if "tb" in condition_name.lower() or "tuberculosis" in condition_name.lower():
                gaps.append(
                    "Mantoux test / IGRA — essential for TB confirmation"
                )

        return gaps