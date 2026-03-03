from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class IntakeStage(str, Enum):
    GREETING           = "greeting"
    CHIEF_COMPLAINT    = "chief_complaint"
    SYMPTOM_DETAIL     = "symptom_detail"
    ASSOCIATED         = "associated_symptoms"
    TIMELINE           = "timeline"
    HISTORY            = "history"
    MEDICATIONS        = "medications"
    REPORTS            = "reports"
    IMAGING            = "imaging"
    CONFIRMING         = "confirming"
    ANALYZING          = "analyzing"
    RESULTS            = "results"


class MessageRole(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"
    SYSTEM    = "system"


class Message(BaseModel):
    message_id: str
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[dict] = None


class ConversationState(BaseModel):
    conversation_id: str
    patient_id: Optional[str] = None
    stage: IntakeStage = IntakeStage.GREETING

    # Chat history
    messages: List[Message] = []

    # ── Structured intake data (filled by user widgets + document parser) ──
    collected_data: Dict = {}

    # ── Uploaded files ──
    reports_uploaded: List[dict] = []     # PDFs / text files + their parsed fields
    images_uploaded: List[dict] = []      # Medical images + their AI findings

    # ── Imaging flags (set by detect_imaging_need) ──
    imaging_needed: bool = False
    imaging_types: List[str] = []

    # ── Final analysis ──
    analysis_result: Optional[dict] = None
    is_complete: bool = False

    created_at: str
    updated_at: str


class ConversationManager:

    def __init__(self):
        self._conversations: Dict[str, ConversationState] = {}

    def create_conversation(
        self, patient_id: Optional[str] = None
    ) -> ConversationState:
        conversation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        state = ConversationState(
            conversation_id=conversation_id,
            patient_id=patient_id,
            stage=IntakeStage.GREETING,
            messages=[],
            collected_data={},
            reports_uploaded=[],
            images_uploaded=[],
            created_at=now,
            updated_at=now
        )
        self._conversations[conversation_id] = state
        return state

    def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationState]:
        return self._conversations.get(conversation_id)

    def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        state = self._conversations.get(conversation_id)
        if not state:
            raise ValueError(f"Conversation {conversation_id} not found")
        message = Message(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        state.messages.append(message)
        state.updated_at = datetime.now().isoformat()
        return message

    def update_stage(self, conversation_id: str, stage: IntakeStage):
        state = self._conversations.get(conversation_id)
        if state:
            state.stage = stage
            state.updated_at = datetime.now().isoformat()

    def update_collected_data(self, conversation_id: str, key: str, value):
        state = self._conversations.get(conversation_id)
        if state:
            state.collected_data[key] = value
            state.updated_at = datetime.now().isoformat()

    def merge_collected_data(self, conversation_id: str, data: dict):
        """Merge a dict into collected_data (used by document parser)."""
        state = self._conversations.get(conversation_id)
        if state:
            for k, v in data.items():
                if v and not state.collected_data.get(k):  # don't overwrite user input
                    state.collected_data[k] = v
            state.updated_at = datetime.now().isoformat()

    def add_report(self, conversation_id: str, report_info: dict):
        """Store a parsed document report."""
        state = self._conversations.get(conversation_id)
        if state:
            state.reports_uploaded.append(report_info)
            state.updated_at = datetime.now().isoformat()

    def add_image(self, conversation_id: str, image_info: dict):
        """Store an analyzed medical image result."""
        state = self._conversations.get(conversation_id)
        if state:
            state.images_uploaded.append(image_info)
            state.updated_at = datetime.now().isoformat()

    def set_imaging_needed(self, conversation_id: str, needed: bool, types: List[str]):
        state = self._conversations.get(conversation_id)
        if state:
            state.imaging_needed = needed
            state.imaging_types = types
            state.updated_at = datetime.now().isoformat()

    def set_analysis_result(self, conversation_id: str, result: dict):
        state = self._conversations.get(conversation_id)
        if state:
            state.analysis_result = result
            state.is_complete = True
            state.stage = IntakeStage.RESULTS
            state.updated_at = datetime.now().isoformat()

    def is_ready_for_analysis(self, conversation_id: str) -> bool:
        state = self._conversations.get(conversation_id)
        if not state:
            return False
        return bool(state.collected_data.get("symptoms_text"))

    def build_analysis_payload(self, conversation_id: str) -> dict:
        """
        Build the unified payload sent to all 3 parallel models.
        Merges: user typed data + parsed document fields + image findings.
        """
        state = self._conversations.get(conversation_id)
        if not state:
            return {}

        payload = dict(state.collected_data)  # base: everything the user typed

        # Merge parsed report fields (don't overwrite user values)
        for report in state.reports_uploaded:
            for k, v in report.get("parsed_fields", {}).items():
                if v and not payload.get(k):
                    payload[k] = v

        # Append image findings to lab_text
        image_summaries = []
        for img in state.images_uploaded:
            findings = img.get("findings", {})
            if findings:
                scan_type = img.get("scan_type", "medical image")
                summary = findings.get("findings") or findings.get("description", "")
                if summary:
                    image_summaries.append(f"[{scan_type.upper()} Analysis] {summary}")

        if image_summaries:
            existing_lab = payload.get("lab_text", "")
            payload["lab_text"] = (existing_lab + "\n" + "\n".join(image_summaries)).strip()

        payload["patient_id"] = state.patient_id or conversation_id
        return payload

    def get_missing_critical_data(self, conversation_id: str) -> List[str]:
        state = self._conversations.get(conversation_id)
        if not state:
            return []
        missing = []
        data = state.collected_data
        if not data.get("symptoms_text"):
            missing.append("symptoms")
        if not data.get("age"):
            missing.append("age")
        if not data.get("symptom_duration"):
            missing.append("how long you've had these symptoms")
        return missing