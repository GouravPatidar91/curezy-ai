"""
Intake engine — deterministic, stage-by-stage doctor-patient conversation.

Key design decisions:
  - Each stage has ONE directive: ask exactly one thing.
  - Any substantive reply (> 2 words) advances the stage — no keyword-gates.
  - After Medications the AI enters CONFIRMING: it summarises findings and
    asks "Shall I proceed with the diagnosis?" Only YES-type replies trigger
    analysis. NO keeps the user in CONFIRMING so they can add more info.
  - Groq is given a tight per-stage system prompt so it NEVER re-asks a
    question that already belongs to a completed stage.
"""

import os
import re
from groq import Groq
from chat.conversation_manager import ConversationManager, MessageRole, IntakeStage

# ---------------------------------------------------------------------------
# Stage ordering
# ---------------------------------------------------------------------------

STAGE_ORDER = [
    IntakeStage.GREETING,
    IntakeStage.CHIEF_COMPLAINT,
    IntakeStage.SYMPTOM_DETAIL,
    IntakeStage.ASSOCIATED,
    IntakeStage.TIMELINE,
    IntakeStage.HISTORY,
    IntakeStage.MEDICATIONS,
    IntakeStage.CONFIRMING,
    IntakeStage.ANALYZING,
    IntakeStage.RESULTS,
]

# ---------------------------------------------------------------------------
# Per-stage directive: what the NEXT question must cover
# ---------------------------------------------------------------------------

STAGE_DIRECTIVE = {
    IntakeStage.CHIEF_COMPLAINT: (
        "Ask the patient ONE open question: what is the main problem or symptom that "
        "brings them here today? Do not ask anything else yet."
    ),
    IntakeStage.SYMPTOM_DETAIL: (
        "The patient described their main problem. Now ask them ONLY about the severity "
        "(on a scale of 1–10) and location of the symptom. Nothing else."
    ),
    IntakeStage.ASSOCIATED: (
        "You know the main symptom, severity and location. Ask ONLY whether they have "
        "any other symptoms alongside it (e.g. fever, nausea, fatigue). "
        "Keep it brief — one question."
    ),
    IntakeStage.TIMELINE: (
        "You know the symptoms. Ask ONLY how long these symptoms have been present and "
        "when exactly they started. One question."
    ),
    IntakeStage.HISTORY: (
        "You know the symptoms and timeline. Ask ONLY about past medical conditions, "
        "previous surgeries, or known allergies. One question."
    ),
    IntakeStage.MEDICATIONS: (
        "You know the medical history. Ask ONLY whether the patient is currently taking "
        "any medications or supplements. One question."
    ),
    IntakeStage.CONFIRMING: (
        "You have gathered all the necessary information. Write a SHORT 3–4 line summary "
        "of what you've learned (symptoms, duration, history, medications). Then ask "
        "'Would you like me to proceed with the diagnosis now?' "
        "Do NOT ask any new medical questions."
    ),
}

# Symptoms that suggest imaging is needed
IMAGING_MAP = {
    "chest pain": "Chest X-Ray",
    "shortness of breath": "Chest X-Ray",
    "back pain": "MRI Spine",
    "headache": "CT Head",
    "head injury": "CT Head",
    "joint pain": "X-Ray Musculoskeletal",
    "abdominal pain": "CT Abdomen",
    "lump": "CT/Ultrasound",
}

# Phrases that mean "yes, go ahead"
YES_PATTERNS = re.compile(
    r"\b(yes|yeah|yep|sure|ok|okay|proceed|go ahead|do it|start|analyze|let'?s go|please|confirm|ready)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------

class IntakeEngine:
    def __init__(self, conversation_manager: ConversationManager):
        self.cm = conversation_manager
        api_key = os.getenv("GROQ_API_KEY")
        self.groq = Groq(api_key=api_key) if api_key else None
        self.model = "llama-3.3-70b-versatile"

    # ── Public helpers ────────────────────────────────────────────────

    def get_greeting(self) -> str:
        return (
            "Hello! 👋 I'm **Curezy AI**, your personal health assistant.\n\n"
            "I'm here to help understand your symptoms and provide you with a detailed "
            "health assessment powered by advanced medical AI.\n\n"
            "⚠️ *This is not a replacement for a doctor. Always consult a qualified physician "
            "for medical decisions.*\n\n"
            "**So, what's bothering you today?** 🩺"
        )

    def get_stage_metadata(self, stage: IntakeStage) -> dict:
        """Minimal metadata the frontend needs for badge / chip hints."""
        meta = {
            IntakeStage.CHIEF_COMPLAINT: {"title": "Chief Complaint",    "can_skip": False},
            IntakeStage.SYMPTOM_DETAIL:  {"title": "Symptom Details",    "can_skip": False},
            IntakeStage.ASSOCIATED:      {"title": "Associated Symptoms", "can_skip": True},
            IntakeStage.TIMELINE:        {"title": "Timeline",            "can_skip": False},
            IntakeStage.HISTORY:         {"title": "Medical History",     "can_skip": True},
            IntakeStage.MEDICATIONS:     {"title": "Medications",         "can_skip": True},
            IntakeStage.CONFIRMING:      {"title": "Ready to Proceed?",   "can_skip": False},
            IntakeStage.ANALYZING:       {"title": "Analyzing…",          "can_skip": False},
            IntakeStage.RESULTS:         {"title": "Results",             "can_skip": False},
        }
        return meta.get(stage, {"title": stage.value.replace("_", " ").title(), "can_skip": False})

    # ── Main entry point ──────────────────────────────────────────────

    def process_message(self, conversation_id: str, user_message: str) -> dict:
        """
        Process one user message. Returns:
          { response, stage, stage_metadata, trigger_analysis }
        """
        state = self.cm.get_conversation(conversation_id)
        if not state:
            return self._error_reply("Conversation not found.")

        current_stage = state.stage
        text = user_message.strip()

        # ── Emergency bypass ──
        if self._is_emergency(text):
            reply = (
                "🚨 **EMERGENCY DETECTED** 🚨\n\n"
                "Based on what you've described, please **call emergency services (112/911) immediately** "
                "or go to the nearest emergency room.\n\n"
                "Do not wait for an AI assessment in this situation."
            )
            self.cm.add_message(conversation_id, MessageRole.ASSISTANT, reply)
            return self._reply(reply, current_stage, False)

        # ── Store user message ──
        self.cm.add_message(conversation_id, MessageRole.USER, text)

        # ── Save data from this message ──
        self._store_stage_data(conversation_id, current_stage, text, state)

        # ── Handle CONFIRMING stage specially ──
        if current_stage == IntakeStage.CONFIRMING:
            if YES_PATTERNS.search(text):
                # User confirmed → trigger analysis
                self.cm.update_stage(conversation_id, IntakeStage.ANALYZING)
                ready_msg = (
                    "Perfect! 🩺 The Curezy Medical Council is now analyzing your case. "
                    "Three AI doctors are reviewing your information in parallel — "
                    "this will take just a moment."
                )
                self.cm.add_message(conversation_id, MessageRole.ASSISTANT, ready_msg)
                return self._reply(ready_msg, "analyzing", True)
            else:
                # Not yet confirmed — let them add more or re-ask
                follow_up = self._groq_follow_up(state, text, current_stage)
                self.cm.add_message(conversation_id, MessageRole.ASSISTANT, follow_up)
                return self._reply(follow_up, "confirming", False)

        # ── Advance stage if current one is satisfied ──
        next_stage = self._next_stage(current_stage, text, state)
        if next_stage != current_stage:
            self.cm.update_stage(conversation_id, next_stage)
            state = self.cm.get_conversation(conversation_id)

            # Check imaging need after symptoms are known
            if next_stage in (IntakeStage.TIMELINE, IntakeStage.ASSOCIATED):
                self._detect_imaging(conversation_id, state)

        # ── Generate response for the next stage ──
        response = self._groq_stage_question(state, next_stage)
        self.cm.add_message(conversation_id, MessageRole.ASSISTANT, response)
        return self._reply(response, next_stage.value, False)

    # ── Stage data storage ────────────────────────────────────────────

    def _store_stage_data(self, conv_id: str, stage: IntakeStage, text: str, state):
        """Map the user's reply to the right field in collected_data."""
        cd = state.collected_data or {}
        if stage == IntakeStage.CHIEF_COMPLAINT and not cd.get("chief_complaint"):
            self.cm.update_collected_data(conv_id, "chief_complaint", text)
            self.cm.update_collected_data(conv_id, "symptoms_text", text)
        elif stage == IntakeStage.SYMPTOM_DETAIL:
            existing = cd.get("symptoms_text", cd.get("chief_complaint", ""))
            self.cm.update_collected_data(conv_id, "symptoms_text", f"{existing}. Detail: {text}")
            # Extract severity number if present
            nums = re.findall(r"\b([1-9]|10)\b", text)
            if nums:
                self.cm.update_collected_data(conv_id, "severity", int(nums[0]))
        elif stage == IntakeStage.ASSOCIATED:
            existing = cd.get("symptoms_text", "")
            self.cm.update_collected_data(conv_id, "symptoms_text", f"{existing}. Associated: {text}")
        elif stage == IntakeStage.TIMELINE:
            self.cm.update_collected_data(conv_id, "duration", text)
            existing = cd.get("symptoms_text", "")
            self.cm.update_collected_data(conv_id, "symptoms_text", f"{existing}. Duration: {text}")
        elif stage == IntakeStage.HISTORY:
            self.cm.update_collected_data(conv_id, "medical_history_text", text)
        elif stage == IntakeStage.MEDICATIONS:
            self.cm.update_collected_data(conv_id, "medications_text", text)

    # ── Stage advancement ─────────────────────────────────────────────

    def _next_stage(self, current: IntakeStage, text: str, state) -> IntakeStage:
        """
        Advance to the next stage if the user gave a substantive reply.
        A reply is substantive if it has > 2 words OR any letters at all.
        We do NOT gate on keywords — any answer moves things forward.
        """
        if len(text.split()) < 1:
            return current

        idx = STAGE_ORDER.index(current) if current in STAGE_ORDER else -1
        if idx < 0 or idx >= len(STAGE_ORDER) - 1:
            return current

        next_s = STAGE_ORDER[idx + 1]

        # Skip ANALYZING and RESULTS — those are triggered differently
        if next_s in (IntakeStage.ANALYZING, IntakeStage.RESULTS):
            return current

        # Skip back to current for GREETING (should never receive user msg here)
        if current == IntakeStage.GREETING:
            return IntakeStage.CHIEF_COMPLAINT

        return next_s

    # ── Groq calls ────────────────────────────────────────────────────

    def _groq_stage_question(self, state, next_stage: IntakeStage) -> str:
        """
        Ask Groq to generate the SINGLE question for `next_stage`,
        given full context of what has already been collected.
        """
        if not self.groq:
            return self._fallback_question(next_stage)

        directive = STAGE_DIRECTIVE.get(next_stage)
        if not directive:
            return self._fallback_question(next_stage)

        cd = state.collected_data or {}
        context_lines = []
        if cd.get("chief_complaint"):
            context_lines.append(f"Chief complaint: {cd['chief_complaint']}")
        if cd.get("symptoms_text") and cd["symptoms_text"] != cd.get("chief_complaint"):
            context_lines.append(f"Symptoms so far: {cd['symptoms_text']}")
        if cd.get("duration"):
            context_lines.append(f"Duration: {cd['duration']}")
        if cd.get("medical_history_text"):
            context_lines.append(f"History: {cd['medical_history_text']}")
        if cd.get("medications_text"):
            context_lines.append(f"Medications: {cd['medications_text']}")

        context = "\n".join(context_lines) if context_lines else "No information collected yet."

        system = (
            "You are a warm, professional medical AI assistant conducting a structured "
            "patient intake interview. You speak like a real doctor — empathetic but focused.\n\n"
            "RULES:\n"
            "1. Ask ONLY the question specified in the directive. Do not ask anything else.\n"
            "2. Do not repeat questions that are already answered (shown in context).\n"
            "3. Be concise — 1–3 sentences maximum.\n"
            "4. Acknowledge the patient's previous answer briefly before asking the next question.\n"
            "5. Never say 'As an AI' or similar disclaimers.\n"
        )

        user_prompt = (
            f"Information already collected:\n{context}\n\n"
            f"Current directive: {directive}"
        )

        try:
            completion = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=200,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"[IntakeEngine] Groq error: {e}")
            return self._fallback_question(next_stage)

    def _groq_follow_up(self, state, user_text: str, stage: IntakeStage) -> str:
        """
        Used ONLY at CONFIRMING stage when user hasn't confirmed yet.
        Re-show summary and re-ask.
        """
        cd = state.collected_data or {}
        summary = self._build_summary(cd)
        return (
            f"{summary}\n\n"
            "Whenever you're ready, just say **'Yes, proceed'** and I'll start the analysis. "
            "Or let me know if you'd like to add anything else."
        )

    # ── Summary building (for CONFIRMING stage) ───────────────────────

    def _build_summary(self, cd: dict) -> str:
        lines = ["Here's a quick summary of what I've gathered:\n"]
        if cd.get("chief_complaint"):
            lines.append(f"• **Main concern:** {cd['chief_complaint']}")
        if cd.get("symptoms_text") and cd["symptoms_text"] != cd.get("chief_complaint"):
            lines.append(f"• **Symptoms:** {cd['symptoms_text']}")
        if cd.get("severity"):
            lines.append(f"• **Severity:** {cd['severity']}/10")
        if cd.get("duration"):
            lines.append(f"• **Duration:** {cd['duration']}")
        if cd.get("medical_history_text"):
            lines.append(f"• **Medical history:** {cd['medical_history_text']}")
        if cd.get("medications_text"):
            lines.append(f"• **Medications:** {cd['medications_text']}")
        lines.append("\nWould you like to **proceed with the diagnosis** now?")
        return "\n".join(lines)

    # ── Fallback questions (Groq unavailable) ─────────────────────────

    def _fallback_question(self, stage: IntakeStage) -> str:
        fallbacks = {
            IntakeStage.CHIEF_COMPLAINT: "What brings you in today? Please describe your main concern.",
            IntakeStage.SYMPTOM_DETAIL: "Where exactly do you feel this and how would you rate the severity on a scale of 1 to 10?",
            IntakeStage.ASSOCIATED: "Are there any other symptoms you're experiencing alongside this — such as fever, nausea, or fatigue?",
            IntakeStage.TIMELINE: "How long have you been experiencing this, and when did it first start?",
            IntakeStage.HISTORY: "Do you have any existing medical conditions, past surgeries, or known allergies?",
            IntakeStage.MEDICATIONS: "Are you currently taking any medications or supplements?",
            IntakeStage.CONFIRMING: "I've gathered all the information I need. Shall I proceed with the diagnosis?",
        }
        return fallbacks.get(stage, "Could you tell me more?")

    # ── Imaging detection ─────────────────────────────────────────────

    def _detect_imaging(self, conv_id: str, state):
        symptoms = (state.collected_data or {}).get("symptoms_text", "").lower()
        for keyword, scan_type in IMAGING_MAP.items():
            if keyword in symptoms:
                self.cm.set_imaging_needed(conv_id, True, [scan_type])
                break

    # ── Emergency detection ───────────────────────────────────────────

    def _is_emergency(self, text: str) -> bool:
        keywords = [
            "can't breathe", "cannot breathe", "chest crushing",
            "severe chest pain", "heart attack", "stroke",
            "unconscious", "unresponsive", "suicide", "overdose",
            "stabbed", "gunshot", "bleeding heavily",
        ]
        t = text.lower()
        return any(k in t for k in keywords)

    # ── Reply helpers ─────────────────────────────────────────────────

    def _reply(self, response: str, stage, trigger_analysis: bool) -> dict:
        stage_val = stage.value if hasattr(stage, "value") else str(stage)
        return {
            "response": response,
            "stage": stage_val,
            "stage_metadata": self.get_stage_metadata(
                IntakeStage(stage_val) if isinstance(stage, str) else stage
            ),
            "trigger_analysis": trigger_analysis,
        }

    def _error_reply(self, msg: str) -> dict:
        return {
            "response": msg,
            "stage": "error",
            "stage_metadata": {},
            "trigger_analysis": False,
        }