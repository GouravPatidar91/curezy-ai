import os
import json
import logging
from datetime import datetime
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    def _serialize(self, obj) -> str:
        if isinstance(obj, list):
            serialized = []
            for item in obj:
                if hasattr(item, 'dict'):
                    serialized.append(item.dict())
                elif isinstance(item, dict):
                    serialized.append(item)
                else:
                    serialized.append(str(item))
            return json.dumps(serialized)
        return json.dumps(obj)

    def log_prediction(
        self,
        patient_id: str,
        patient_state: dict,
        clinical_analysis: dict,
        doctor_id: Optional[str] = None
    ) -> dict:
        try:
            top_conditions = clinical_analysis.get("top_3_conditions", [])
            serialized_conditions = []
            for c in top_conditions:
                if hasattr(c, 'dict'):
                    serialized_conditions.append(c.dict())
                elif isinstance(c, dict):
                    serialized_conditions.append(c)

            log_entry = {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "timestamp": datetime.now().isoformat(),
                "symptoms": json.dumps(patient_state.get("symptoms", [])),
                "top_conditions": json.dumps(serialized_conditions),
                "consensus_confidence": float(
                    clinical_analysis.get("consensus_confidence", 0)
                ),
                "agents_agreed": bool(
                    clinical_analysis.get("agents_agreed", True)
                ),
                "safety_flags": json.dumps(
                    clinical_analysis.get("safety_flags", [])
                ),
                "doctor_review_required": bool(
                    clinical_analysis.get("doctor_review_required", True)
                ),
                "missing_data_suggestions": json.dumps(
                    clinical_analysis.get("missing_data_suggestions", [])
                ),
                "data_completeness_score": float(
                    patient_state.get("data_completeness_score", 0)
                ),
                "status": "pending_review"
            }

            result = self.supabase.table("audit_logs").insert(log_entry).execute()
            return {"success": True, "log_id": result.data[0]["id"]}

        except Exception as e:
            self._log_locally(log_entry if 'log_entry' in locals() else {})
            logger.error(f"[Audit] Failed to log prediction: {e}")
            return {"success": False, "error": str(e)}

    def _log_locally(self, entry: dict):
        """Fallback: append failed entries to a local JSONL file."""
        try:
            os.makedirs("audit_fallback", exist_ok=True)
            with open("audit_fallback/failed_logs.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as fe:
            logger.error(f"[Audit] Local fallback also failed: {fe}")

    def record_doctor_feedback(
        self,
        log_id: str,
        actual_diagnosis: str,
        ai_was_correct: bool,
        doctor_notes: Optional[str] = None,
        doctor_id: Optional[str] = None
    ) -> dict:
        try:
            update = {
                "actual_diagnosis": actual_diagnosis,
                "ai_was_correct": ai_was_correct,
                "doctor_notes": doctor_notes,
                "status": "reviewed",
                "reviewed_at": datetime.now().isoformat()
            }
            if doctor_id:
                update["doctor_id"] = doctor_id
            self.supabase.table("audit_logs").update(update).eq(
                "id", log_id
            ).execute()
            return {"success": True}

        except Exception as e:
            logger.error(f"[Audit] Failed to record feedback: {e}")
            return {"success": False, "error": str(e)}

    def get_patient_history(self, patient_id: str) -> list:
        try:
            result = self.supabase.table("audit_logs").select("*").eq(
                "patient_id", patient_id
            ).order("timestamp", desc=True).execute()
            return result.data

        except Exception as e:
            logger.error(f"[Audit] Failed to get history: {e}")
            return []