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
    IntakeStage.BASIC_INFO,
    IntakeStage.CHIEF_COMPLAINT,
    IntakeStage.OPQRST_ONSET,
    IntakeStage.OPQRST_PROVOCATION,
    IntakeStage.OPQRST_QUALITY,
    IntakeStage.OPQRST_REGION,
    IntakeStage.OPQRST_SEVERITY,
    IntakeStage.OPQRST_TIMING,
    IntakeStage.ASSOCIATED,
    IntakeStage.HISTORY,
    IntakeStage.MEDICATIONS,
    IntakeStage.ALLERGIES,
    IntakeStage.LIFESTYLE,
    IntakeStage.FAMILY_HISTORY,
    IntakeStage.RED_FLAGS,
    IntakeStage.REPORTS,
    IntakeStage.CONFIRMING,
    IntakeStage.ANALYZING,
    IntakeStage.RESULTS,
]

# ---------------------------------------------------------------------------
# Per-stage directive: what the NEXT question must cover
# ---------------------------------------------------------------------------

STAGE_DIRECTIVE = {
    IntakeStage.BASIC_INFO: (
        "Ask the patient for their BASIC information: age, gender, and current location. "
        "Ask this in one friendly sentence."
    ),
    IntakeStage.CHIEF_COMPLAINT: (
        "Ask the patient ONE open question: what is the main problem or symptom that "
        "brings them here today? Do not ask anything else yet."
    ),
    IntakeStage.OPQRST_ONSET: (
        "Onset: Ask the patient WHEN exactly the symptom first began and if it started suddenly or gradually."
    ),
    IntakeStage.OPQRST_PROVOCATION: (
        "Provocation / Palliation: Ask the patient what makes the symptom better or worse (e.g. activity, rest, eating)."
    ),
    IntakeStage.OPQRST_QUALITY: (
        "Quality: Ask the patient to describe the sensation (e.g. sharp, dull, throbbing, burning)."
    ),
    IntakeStage.OPQRST_REGION: (
        "Region / Radiation: Ask WHERE exactly the symptom is and if it spreads to another area."
    ),
    IntakeStage.OPQRST_SEVERITY: (
        "Severity: Ask the patient to rate the severity on a scale of 1–10 (1=mild, 10=worst)."
    ),
    IntakeStage.OPQRST_TIMING: (
        "Timing: Ask how often the symptom occurs (constant, intermittent, getting worse, improving)."
    ),
    IntakeStage.ASSOCIATED: (
        "Associated Symptoms: Ask whether they have any other symptoms alongside it (e.g. nausea, light sensitivity, fever). "
        "Customize your suggestion based on the chief complaint (e.g. if headache, suggest nausea)."
    ),
    IntakeStage.HISTORY: (
        "Medical History: Ask if they have any known medical conditions like diabetes, hypertension, or asthma."
    ),
    IntakeStage.MEDICATIONS: (
        "Medications: Ask if they are currently taking any medications, including dosage and frequency."
    ),
    IntakeStage.ALLERGIES: (
        "Allergies: Ask if they have any allergies to medications, foods, or environmental factors."
    ),
    IntakeStage.LIFESTYLE: (
        "Lifestyle: Ask about lifestyle factors: smoking, alcohol consumption, exercise, and sleep hours."
    ),
    IntakeStage.FAMILY_HISTORY: (
        "Family History: Ask about hereditary diseases in the family (e.g. heart disease, diabetes, cancer)."
    ),
    IntakeStage.RED_FLAGS: (
        "Red-Flag Screening: Perform a final check for any dangerous 'red-flag' symptoms they might have missed "
        "(e.g. sudden weakness, crushing chest pain, speech difficulty)."
    ),
    IntakeStage.CONFIRMING: (
        "You have gathered all the necessary information. Write a SHORT 3–4 line summary "
        "of what you've learned. Then ask 'Would you like me to proceed with the diagnosis now?'"
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
            IntakeStage.BASIC_INFO:         {"title": "Personal info",       "can_skip": False},
            IntakeStage.CHIEF_COMPLAINT:    {"title": "Chief Complaint",    "can_skip": False},
            IntakeStage.OPQRST_ONSET:       {"title": "Onset",               "can_skip": False},
            IntakeStage.OPQRST_PROVOCATION: {"title": "Provocation",         "can_skip": False},
            IntakeStage.OPQRST_QUALITY:     {"title": "Quality",             "can_skip": False},
            IntakeStage.OPQRST_REGION:      {"title": "Location",            "can_skip": False},
            IntakeStage.OPQRST_SEVERITY:    {"title": "Severity",            "can_skip": False},
            IntakeStage.OPQRST_TIMING:      {"title": "Timing",              "can_skip": False},
            IntakeStage.ASSOCIATED:         {"title": "Associated",          "can_skip": True},
            IntakeStage.HISTORY:            {"title": "Medical History",     "can_skip": True},
            IntakeStage.MEDICATIONS:        {"title": "Medications",         "can_skip": True},
            IntakeStage.ALLERGIES:          {"title": "Allergies",           "can_skip": True},
            IntakeStage.LIFESTYLE:          {"title": "Lifestyle",           "can_skip": True},
            IntakeStage.FAMILY_HISTORY:     {"title": "Family History",      "can_skip": True},
            IntakeStage.RED_FLAGS:          {"title": "Safety Check",        "can_skip": False},
            IntakeStage.REPORTS:            {"title": "Reports",             "can_skip": True},
            IntakeStage.CONFIRMING:         {"title": "Ready?",             "can_skip": False},
            IntakeStage.ANALYZING:          {"title": "Analyzing…",          "can_skip": False},
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
            if next_stage in (IntakeStage.OPQRST_TIMING, IntakeStage.ASSOCIATED):
                self._detect_imaging(conversation_id, state)

        # ── Generate response for the next stage ──
        response = self._groq_stage_question(state, next_stage)
        self.cm.add_message(conversation_id, MessageRole.ASSISTANT, response)
        return self._reply(response, next_stage.value, False)

    # ── Stage data storage ────────────────────────────────────────────

    def _store_stage_data(self, conv_id: str, stage: IntakeStage, text: str, state):
        """Map the user's reply to the right field in collected_data."""
        cd = state.collected_data or {}
        
        if stage == IntakeStage.BASIC_INFO:
            # We trust Groq's question prompted for: age, gender, location
            # For simplicity, we store the full text; clinical reasoner will parse later.
            self.cm.update_collected_data(conv_id, "patient_info_raw", text)
            # Basic regex for age
            age_match = re.search(r"(\d{1,2})", text)
            if age_match: self.cm.update_collected_data(conv_id, "age", int(age_match.group(1)))
            if "male" in text.lower(): self.cm.update_collected_data(conv_id, "gender", "male")
            elif "female" in text.lower(): self.cm.update_collected_data(conv_id, "gender", "female")

        elif stage == IntakeStage.CHIEF_COMPLAINT:
            self.cm.update_collected_data(conv_id, "chief_complaint", text)
            
        elif stage == IntakeStage.OPQRST_ONSET:
            self.cm.update_collected_data(conv_id, "onset", text)
        elif stage == IntakeStage.OPQRST_PROVOCATION:
            self.cm.update_collected_data(conv_id, "provocation", text)
        elif stage == IntakeStage.OPQRST_QUALITY:
            self.cm.update_collected_data(conv_id, "quality", text)
        elif stage == IntakeStage.OPQRST_REGION:
            self.cm.update_collected_data(conv_id, "region", text)
        elif stage == IntakeStage.OPQRST_SEVERITY:
            nums = re.findall(r"\b([1-9]|10)\b", text)
            if nums: self.cm.update_collected_data(conv_id, "severity", int(nums[0]))
            else: self.cm.update_collected_data(conv_id, "severity_text", text)
        elif stage == IntakeStage.OPQRST_TIMING:
            self.cm.update_collected_data(conv_id, "timing", text)

        elif stage == IntakeStage.ASSOCIATED:
            self.cm.update_collected_data(conv_id, "associated_symptoms", text)
        elif stage == IntakeStage.HISTORY:
            self.cm.update_collected_data(conv_id, "medical_history_text", text)
        elif stage == IntakeStage.MEDICATIONS:
            self.cm.update_collected_data(conv_id, "medications_text", text)
        elif stage == IntakeStage.ALLERGIES:
            self.cm.update_collected_data(conv_id, "allergies", text)
        elif stage == IntakeStage.LIFESTYLE:
            self.cm.update_collected_data(conv_id, "lifestyle_raw", text)
        elif stage == IntakeStage.FAMILY_HISTORY:
            self.cm.update_collected_data(conv_id, "family_history", text)
        elif stage == IntakeStage.RED_FLAGS:
            self.cm.update_collected_data(conv_id, "red_flags_raw", text)
            if self._is_emergency(text):
                self.cm.update_collected_data(conv_id, "red_flag_detected", True)

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
            IntakeStage.GREETING: "Hello! How can I help you today?",
            IntakeStage.BASIC_INFO: "To provide the best advice, could you please tell me your age, gender, and general location?",
            IntakeStage.CHIEF_COMPLAINT: "What brings you in today? Please describe your main concern.",
            IntakeStage.OPQRST_ONSET: "When did this symptom first start?",
            IntakeStage.OPQRST_PROVOCATION: "What makes the symptom better or worse?",
            IntakeStage.OPQRST_QUALITY: "What does the symptom feel like? (e.g., sharp, dull ache, burning)",
            IntakeStage.OPQRST_REGION: "Where exactly is the symptom located, and does it spread anywhere?",
            IntakeStage.OPQRST_SEVERITY: "On a scale of 1 to 10, how severe is the symptom?",
            IntakeStage.OPQRST_TIMING: "Is the symptom constant, or does it come and go?",
            IntakeStage.ASSOCIATED: "Are there any other symptoms you're experiencing alongside this?",
            IntakeStage.HISTORY: "Do you have any existing medical conditions or past surgeries?",
            IntakeStage.MEDICATIONS: "Are you currently taking any medications or supplements?",
            IntakeStage.ALLERGIES: "Do you have any known allergies?",
            IntakeStage.LIFESTYLE: "Could you tell me about your lifestyle habits (e.g., smoking, alcohol)?",
            IntakeStage.FAMILY_HISTORY: "Is there any relevant medical history in your family?",
            IntakeStage.RED_FLAGS: "Have you noticed any severe symptoms like sudden weakness or difficulty breathing?",
            IntakeStage.CONFIRMING: "I've gathered all the information I need. Shall I proceed with the diagnosis?",
        }
        return fallbacks.get(stage, "Could you tell me more?")

    # ── Imaging detection ─────────────────────────────────────────────

    def _detect_imaging(self, conv_id: str, state):
        cd = state.collected_data or {}
        # Scan chief complaint, region, and associated symptoms for imaging keywords
        search_text = " ".join([
            str(cd.get("chief_complaint", "")),
            str(cd.get("region", "")),
            str(cd.get("associated_symptoms", ""))
        ]).lower()
        
        for keyword, scan_type in IMAGING_MAP.items():
            if keyword in search_text:
                self.cm.set_imaging_needed(conv_id, True, [scan_type])
                break

    # ── Emergency detection ───────────────────────────────────────────

    def _is_emergency(self, text: str) -> bool:
        keywords = [
            # Cardiovascular
            "crushing chest pain", "chest pain with arm radiation", "severe shortness of breath",
            "heart attack", "can't breathe", "cannot breathe",
            # Neurological
            "sudden weakness", "facial drooping", "speech difficulty", "severe sudden headache",
            "stroke", "unconscious", "unresponsive", "loss of consciousness",
            # Infection / Trauma
            "high fever with stiff neck", "confusion with fever",
            "severe bleeding", "stabbed", "gunshot",
            # Psychiatric
            "suicide", "overdose",
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