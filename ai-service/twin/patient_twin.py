from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class VisitSnapshot(BaseModel):
    visit_id: str
    patient_id: str
    timestamp: str
    symptoms: List[str]
    top_condition: str
    confidence: float
    lab_highlights: List[dict]
    risk_factors: List[str]
    doctor_review_required: bool

class TrendAlert(BaseModel):
    alert_type: str        # WORSENING, IMPROVING, NEW_SYMPTOM, RECURRING
    message: str
    severity: str          # LOW, MEDIUM, HIGH
    triggered_by: str

class PatientTwin(BaseModel):
    patient_id: str
    total_visits: int
    first_seen: str
    last_seen: str
    recurring_symptoms: List[str]
    recurring_conditions: List[str]
    worsening_labs: List[str]
    trend_alerts: List[TrendAlert]
    visit_history: List[VisitSnapshot]
    health_trajectory: str   # IMPROVING, STABLE, WORSENING, CRITICAL


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _flatten_to_str(value) -> str:
    """Convert any value to a plain string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("name") or value.get("condition") or str(value)
    return str(value)


# ─────────────────────────────────────────
# PATIENT TWIN ENGINE
# ─────────────────────────────────────────

class PatientTwinEngine:

    def __init__(self):
        try:
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            self._ensure_table()
        except Exception as e:
            print(f"[Twin] Supabase init failed: {e}")
            self.supabase = None

    def _ensure_table(self):
        # Table is created via Supabase dashboard
        # patient_visits: id, patient_id, timestamp, symptoms,
        #   top_condition, confidence, lab_highlights,
        #   risk_factors, doctor_review_required
        pass

    def record_visit(
        self,
        patient_state: dict,
        clinical_analysis: dict,
        audit_log_id: str
    ) -> VisitSnapshot:

        # ── Flatten symptoms (may be strings or dicts)
        raw_symptoms = patient_state.get("symptoms", [])
        flat_symptoms = [_flatten_to_str(s) for s in raw_symptoms]

        # ── Flatten risk factors (may be strings or dicts)
        raw_risks = patient_state.get("risk_factors", [])
        flat_risks = [_flatten_to_str(r) for r in raw_risks]

        # ── Top condition
        top_conditions = clinical_analysis.get("top_3_conditions", [])
        top_condition = (
            top_conditions[0].get("condition", "Unknown")
            if top_conditions else "Unknown"
        )

        # ── Lab highlights (safe serialization)
        lab_highlights = [
            {
                "test": str(lab.get("test_name", "")),
                "value": str(lab.get("value", "")),
                "abnormal": bool(lab.get("is_abnormal", False))
            }
            for lab in patient_state.get("lab_reports", [])
        ]

        snapshot = VisitSnapshot(
            visit_id=audit_log_id,
            patient_id=patient_state["patient_id"],
            timestamp=patient_state.get("timestamp", datetime.now().isoformat()),
            symptoms=flat_symptoms,
            top_condition=top_condition,
            confidence=clinical_analysis.get("consensus_confidence", 0),
            lab_highlights=lab_highlights,
            risk_factors=flat_risks,
            doctor_review_required=clinical_analysis.get("doctor_review_required", False)
        )

        # ── Save to Supabase
        if self.supabase:
            try:
                self.supabase.table("patient_visits").insert({
                    "visit_id": snapshot.visit_id,
                    "patient_id": snapshot.patient_id,
                    "timestamp": snapshot.timestamp,
                    "symptoms": snapshot.symptoms,
                    "top_condition": snapshot.top_condition,
                    "confidence": snapshot.confidence,
                    "lab_highlights": lab_highlights,
                    "risk_factors": snapshot.risk_factors,
                    "doctor_review_required": snapshot.doctor_review_required
                }).execute()
                print(f"[Twin] Visit recorded for patient {snapshot.patient_id}")
            except Exception as e:
                print(f"[Twin] Failed to save visit: {e}")

        return snapshot

    def get_patient_twin(self, patient_id: str) -> Optional[PatientTwin]:
        if not self.supabase:
            return None

        try:
            result = self.supabase.table("patient_visits") \
                .select("*") \
                .eq("patient_id", patient_id) \
                .order("timestamp") \
                .execute()

            visits_data = result.data
            if not visits_data:
                return None

            visits = [VisitSnapshot(**v) for v in visits_data]

            # ── Analyze patterns
            all_symptoms = [s for v in visits for s in v.symptoms]
            all_conditions = [v.top_condition for v in visits]

            recurring_symptoms = list({
                s for s in all_symptoms
                if all_symptoms.count(s) > 1
            })
            recurring_conditions = list({
                c for c in all_conditions
                if all_conditions.count(c) > 1
            })

            alerts = self._detect_trends(visits)
            trajectory = self._calculate_trajectory(visits)
            worsening_labs = self._detect_worsening_labs(visits)

            return PatientTwin(
                patient_id=patient_id,
                total_visits=len(visits),
                first_seen=visits[0].timestamp,
                last_seen=visits[-1].timestamp,
                recurring_symptoms=recurring_symptoms,
                recurring_conditions=recurring_conditions,
                worsening_labs=worsening_labs,
                trend_alerts=alerts,
                visit_history=visits,
                health_trajectory=trajectory
            )

        except Exception as e:
            print(f"[Twin] Failed to get twin: {e}")
            return None

    def _detect_trends(self, visits: List[VisitSnapshot]) -> List[TrendAlert]:
        alerts = []

        if len(visits) < 2:
            return alerts

        latest = visits[-1]
        previous = visits[-2]

        # Confidence dropping = condition worsening
        if latest.confidence < previous.confidence - 15:
            alerts.append(TrendAlert(
                alert_type="WORSENING",
                message=f"Diagnostic confidence dropped from {previous.confidence}% to {latest.confidence}%",
                severity="HIGH",
                triggered_by="confidence_drop"
            ))

        # New symptoms appeared
        new_symptoms = set(latest.symptoms) - set(previous.symptoms)
        if new_symptoms:
            alerts.append(TrendAlert(
                alert_type="NEW_SYMPTOM",
                message=f"New symptoms detected: {', '.join(new_symptoms)}",
                severity="MEDIUM",
                triggered_by="symptom_change"
            ))

        # Same condition recurring
        if latest.top_condition == previous.top_condition:
            alerts.append(TrendAlert(
                alert_type="RECURRING",
                message=f"{latest.top_condition} appearing in consecutive visits",
                severity="MEDIUM",
                triggered_by="recurring_condition"
            ))

        # Confidence improving
        if latest.confidence > previous.confidence + 10:
            alerts.append(TrendAlert(
                alert_type="IMPROVING",
                message=f"Diagnostic confidence improved from {previous.confidence}% to {latest.confidence}%",
                severity="LOW",
                triggered_by="confidence_improvement"
            ))

        return alerts

    def _calculate_trajectory(self, visits: List[VisitSnapshot]) -> str:
        if len(visits) < 2:
            return "STABLE"

        recent = visits[-3:] if len(visits) >= 3 else visits
        confidences = [v.confidence for v in recent]
        dr_reviews = [v.doctor_review_required for v in recent]

        avg_change = (confidences[-1] - confidences[0]) / len(confidences)

        if any(dr_reviews[-2:]):
            return "CRITICAL"
        elif avg_change > 5:
            return "IMPROVING"
        elif avg_change < -5:
            return "WORSENING"
        else:
            return "STABLE"

    def _detect_worsening_labs(self, visits: List[VisitSnapshot]) -> List[str]:
        worsening = []
        if len(visits) < 2:
            return worsening

        latest_labs = {
            lab["test"]: lab
            for lab in visits[-1].lab_highlights
        }
        prev_labs = {
            lab["test"]: lab
            for lab in visits[-2].lab_highlights
        }

        for test, lab in latest_labs.items():
            if test in prev_labs:
                if lab["abnormal"] and not prev_labs[test]["abnormal"]:
                    worsening.append(
                        f"{test} became abnormal since last visit"
                    )

        return worsening