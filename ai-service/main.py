from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Header
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from preprocessing.patient_preprocessor import PatientPreprocessor
from agents.clinical_reasoner import ClinicalReasoner
from confidence.uncertainty_engine import UncertaintyEngine
from audit.audit_logger import AuditLogger
from twin.patient_twin import PatientTwinEngine
from security.auth import (
    authenticate_user, create_access_token,
    get_current_user, require_doctor, require_admin
)
from imaging.xray_analyzer import ChestXRayAnalyzer
from security.rate_limiter import limiter, rate_limit_exceeded_handler
from security.api_key_manager import APIKeyManager
from chat.conversation_manager import ConversationManager, MessageRole, IntakeStage
from chat.intake_engine import IntakeEngine
from chat.document_parser import DocumentParser
from finetune.pipeline import start_pipeline, get_job, list_jobs
from finetune.deploy import OllamaDeploy
import logging


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] not in ("/benchmark/status", "/finetune/status")

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

# ── Init app
app = FastAPI(
    title="Curezy AI Service",
    description="Doctor-supervised clinical intelligence API",
    version="1.0.0"
)

# ── Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Services
preprocessor         = PatientPreprocessor()
reasoner             = ClinicalReasoner()
uncertainty_engine   = UncertaintyEngine()
audit_logger         = AuditLogger()
twin_engine          = PatientTwinEngine()
api_key_manager      = APIKeyManager()
conversation_manager = ConversationManager()
intake_engine        = IntakeEngine(conversation_manager)
document_parser      = DocumentParser()
xray_analyzer        = ChestXRayAnalyzer()

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")



# ─────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────

class PatientInput(BaseModel):
    patient_id: str
    symptoms_text: str
    medical_history_text: Optional[str] = ""
    lab_text: Optional[str] = ""
    medications_text: Optional[str] = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    doctor_id: Optional[str] = None

class LoginInput(BaseModel):
    username: str
    password: str

class FeedbackInput(BaseModel):
    audit_log_id: str
    actual_diagnosis: str
    ai_was_correct: bool
    doctor_notes: Optional[str] = ""

class CouncilFeedbackInput(BaseModel):
    """Patient/doctor feedback submitted from the chat UI FeedbackBar."""
    session_id: str                          # backend conversation_id  
    patient_id: Optional[str] = None
    rating: int                              # 1–5 stars
    actual_diagnosis: Optional[str] = None  # if doctor corrects it
    doctor_verified: Optional[bool] = False
    feedback_notes: Optional[str] = ""


class GenerateKeyInput(BaseModel):
    name: str
    client: str
    permissions: Optional[list] = ["analyze", "preprocess"]
    rate_limit: Optional[int] = 100

class ChatInput(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    patient_id: Optional[str] = None
    selected_model: Optional[str] = None  # 'council' | 'medgemma' | 'openbiollm' | 'mistral'

class ChatStructuredInput(BaseModel):
    conversation_id: str
    stage: str
    data: dict  # widget-submitted structured data

class ChatCompletionMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatCompletionMessage]
    temperature: Optional[float] = 1.0
    stream: Optional[bool] = False


# ─────────────────────────────────────────
# AUTH ROUTES (public)
# ─────────────────────────────────────────

@app.post("/auth/login")
def login(data: LoginInput):
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({
        "sub": user["user_id"],
        "role": user["role"],
        "hospital_id": user.get("hospital_id")
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "user_id": user["user_id"]
    }


# ─────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "Curezy AI", "status": "running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": str(__import__("datetime").datetime.now())}


# ─────────────────────────────────────────
# PROTECTED ROUTES
# ─────────────────────────────────────────

@app.post("/preprocess")
@limiter.limit("30/minute")
def preprocess_patient(
    request: Request,
    data: PatientInput,
    current_user: dict = Depends(get_current_user)
):
    try:
        patient_state = preprocessor.process(
            patient_id=data.patient_id,
            symptoms_text=data.symptoms_text,
            medical_history_text=data.medical_history_text,
            lab_text=data.lab_text,
            medications_text=data.medications_text,
            age=data.age,
            gender=data.gender
        )
        return {"success": True, "patient_state": patient_state.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
@limiter.limit("10/minute")
def analyze_patient(
    request: Request,
    data: PatientInput,
    current_user: dict = Depends(get_current_user)
):
    try:
        from utils.runpod_client import RunpodClient
        rpc = RunpodClient()

        if rpc.is_configured:
            print("[REST] ☁️ Active RunPod credentials detected. Forwarding to Cloud GPU...")
            
            runpod_payload = {
                "patient_id": data.patient_id,
                "symptoms_text": data.symptoms_text,
                "medical_history_text": data.medical_history_text,
                "lab_text": data.lab_text,
                "medications_text": data.medications_text,
                "age": data.age,
                "gender": data.gender
            }
            
            # Send to RunPod Serverless GPU
            import asyncio
            rp_result = asyncio.run(rpc.run_council_analysis(
                patient_state=runpod_payload,
                mode="council",
                model_key=None
            ))
            
            patient_state_dict = rp_result.get("patient_state", {})
            clinical_output_dict = rp_result.get("clinical_analysis", {})
            confidence_report_dict = rp_result.get("confidence_report", {})
            
            data_gaps = uncertainty_engine.generate_active_data_gaps(
                patient_state_dict, clinical_output_dict
            )

        else:
            print("[REST] 💻 No RunPod credentials found. Running AI Council locally...")
            
            patient_state = preprocessor.process(
                patient_id=data.patient_id,
                symptoms_text=data.symptoms_text,
                medical_history_text=data.medical_history_text,
                lab_text=data.lab_text,
                medications_text=data.medications_text,
                age=data.age,
                gender=data.gender
            )
            patient_state_dict = patient_state.dict()

            clinical_output = reasoner.analyze(patient_state_dict)
            clinical_output_dict = clinical_output.dict()

            confidence_report = uncertainty_engine.analyze_clinical_confidence(
                patient_state_dict, clinical_output_dict
            )
            confidence_report_dict = confidence_report.dict()

            data_gaps = uncertainty_engine.generate_active_data_gaps(
                patient_state_dict, clinical_output_dict
            )

        # Step 5 — Audit log
        log_result = audit_logger.log_prediction(
            patient_id=data.patient_id,
            patient_state=patient_state_dict,
            clinical_analysis=clinical_output_dict,
            doctor_id=current_user["user_id"]
        )

        # Step 6 — Digital twin
        twin_engine.record_visit(
            patient_state=patient_state_dict,
            clinical_analysis=clinical_output_dict,
            audit_log_id=log_result.get("log_id", "unknown")
        )

        return {
            "success": True,
            "requested_by": current_user["user_id"],
            "patient_state": patient_state_dict,
            "clinical_analysis": clinical_output_dict,
            "confidence_report": confidence_report_dict,
            "active_data_gaps": data_gaps,
            "audit_log_id": log_result.get("log_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
@limiter.limit("20/minute")
def submit_feedback(
    request: Request,
    data: FeedbackInput,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = audit_logger.record_doctor_feedback(
            log_id=data.audit_log_id,
            actual_diagnosis=data.actual_diagnosis,
            ai_was_correct=data.ai_was_correct,
            doctor_notes=data.doctor_notes,
            doctor_id=current_user["user_id"]
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patient/{patient_id}/history")
@limiter.limit("20/minute")
def get_patient_history(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    history = audit_logger.get_patient_history(patient_id)
    return {"success": True, "history": history, "count": len(history)}


@app.get("/patient/{patient_id}/twin")
@limiter.limit("20/minute")
def get_patient_twin(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    twin = twin_engine.get_patient_twin(patient_id)
    if not twin:
        return {"success": False, "message": "No visit history found"}
    return {"success": True, "twin": twin.dict()}


@app.post("/analyze/xray")
@limiter.limit("5/minute")
async def analyze_xray(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        temp_dir = os.path.join(os.path.dirname(__file__), ".tmp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = xray_analyzer.analyze(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────
# API KEY MANAGEMENT
# Any authenticated user can generate keys
# ─────────────────────────────────────────

@app.post("/admin/apikey/generate")
@limiter.limit("10/minute")
def generate_api_key(
    request: Request,
    data: GenerateKeyInput,
    current_user: dict = Depends(get_current_user)
):
    try:
        key_data = api_key_manager.generate_key(
            name=data.name,
            client=data.client,
            permissions=data.permissions,
            rate_limit=data.rate_limit
        )
        return {
            "success": True,
            "api_key": key_data["api_key"],
            "key_id": key_data["key_id"],
            "name": key_data["name"],
            "warning": "Store this key safely — it won't be shown again"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/apikey/list")
@limiter.limit("10/minute")
def list_api_keys(
    request: Request,
    current_user: dict = Depends(get_current_user)  # ← any authenticated user
):
    try:
        keys = api_key_manager.list_keys()
        return {"success": True, "keys": keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/apikey/{key_id}/revoke")
@limiter.limit("10/minute")
def revoke_api_key(
    request: Request,
    key_id: str,
    current_user: dict = Depends(get_current_user)  # ← any authenticated user
):
    try:
        success = api_key_manager.revoke_key(key_id)
        return {"success": success, "key_id": key_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ───────────────────────────────────────
# CHAT ROUTES
# ───────────────────────────────────────

CHAT_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "temp_uploads")
os.makedirs(CHAT_UPLOAD_DIR, exist_ok=True)

ALLOWED_DOC_EXTS   = {".pdf", ".txt", ".docx"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".dcm"}


@app.post("/chat/start")
@limiter.limit("20/minute")
def start_conversation(
    request: Request,
    patient_id: Optional[str] = None
):
    """Create a new conversation and return the greeting + Stage 1 metadata."""
    state = conversation_manager.create_conversation(patient_id)
    greeting = intake_engine.get_greeting()
    conversation_manager.add_message(
        conversation_id=state.conversation_id,
        role=MessageRole.ASSISTANT,
        content=greeting
    )
    stage_meta = intake_engine.get_stage_metadata(state.stage)
    return {
        "success": True,
        "conversation_id": state.conversation_id,
        "message": greeting,
        "stage": state.stage.value,
        "stage_metadata": stage_meta,
    }


@app.post("/chat/message")
@limiter.limit("30/minute")
async def send_chat_message(
    request: Request,
    data: ChatInput
):
    """Process a free-text message and return next stage metadata."""
    if not data.conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id required")

    state = conversation_manager.get_conversation(data.conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = intake_engine.process_message(
        conversation_id=data.conversation_id,
        user_message=data.message
    )

    if result["trigger_analysis"]:
        return await _run_council_analysis(data.conversation_id, state, data.selected_model)

    return {
        "success": True,
        "message": result["response"],
        "stage": result["stage"],
        "stage_metadata": result["stage_metadata"],
    }


@app.post("/chat/stage-submit")
@limiter.limit("30/minute")
async def submit_stage(
    request: Request,
    data: ChatStructuredInput
):
    """
    Frontend submits structured widget data (chips, slider, tag list etc.).
    Returns next stage + metadata.
    """
    state = conversation_manager.get_conversation(data.conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = intake_engine.process_structured_input(
        conversation_id=data.conversation_id,
        stage=data.stage,
        data=data.data
    )

    if result["trigger_analysis"]:
        return await _run_council_analysis(data.conversation_id, state)

    return {
        "success": True,
        "message": result["response"],
        "stage": result["stage"],
        "stage_metadata": result["stage_metadata"],
    }


@app.post("/chat/upload-report")
@limiter.limit("10/minute")
async def upload_report(
    request: Request,
    conversation_id: str,
    file: UploadFile = File(...)
):
    """
    Upload a document (PDF/TXT/DOCX) or medical image (JPG/PNG).
    - Documents: extracted via Groq → returns parsed_fields
    - Images: analyzed via xray_analyzer → returns image_findings
    Advances the conversation stage if appropriate.
    """
    import re as _re

    state = conversation_manager.get_conversation(conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_DOC_EXTS and ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: PDF, TXT, DOCX, JPG, PNG"
        )

    safe_name = _re.sub(r"[^\w\-_.]", "_", file.filename or "upload")[:100]
    save_path = os.path.join(CHAT_UPLOAD_DIR, f"{conversation_id}_{safe_name}")

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # — Document: Groq extraction —
    if ext in ALLOWED_DOC_EXTS:
        try:
            parse_result = document_parser.process_file(save_path, file.filename)
        except Exception as e:
            print(f"[UploadReport] Document parsing error: {e}")
            parse_result = {"success": False, "error": str(e), "parsed_fields": {}}

        report_info = {
            "filename": file.filename,
            "file_size": len(content),
            "parsed_fields": parse_result.get("parsed_fields", {}),
            "success": parse_result.get("success", False),
        }
        conversation_manager.add_report(conversation_id, report_info)
        # Merge extracted fields into collected_data (fills gaps without overwriting user input)
        conversation_manager.merge_collected_data(
            conversation_id, parse_result.get("parsed_fields", {})
        )

        return {
            "success": True,
            "type": "document",
            "filename": file.filename,
            "parsed_fields": parse_result.get("parsed_fields", {}),
            "extraction_success": parse_result.get("success", False),
            "message": (
                "Document uploaded and medical information extracted."
                if parse_result.get("success")
                else "Document uploaded but extraction had issues — your report is still saved."
            ),
        }

    # — Medical Image: analyzer —
    else:
        try:
            findings = xray_analyzer.analyze(save_path)
        except Exception as e:
            findings = {"success": False, "error": str(e)}

        # Detect scan type from filename or stage context
        imaging_types = state.imaging_types
        scan_type = imaging_types[0] if imaging_types else "medical_image"

        image_info = {
            "filename": file.filename,
            "file_size": len(content),
            "scan_type": scan_type,
            "findings": findings,
            "success": findings.get("success", False),
        }
        conversation_manager.add_image(conversation_id, image_info)

        return {
            "success": True,
            "type": "image",
            "filename": file.filename,
            "scan_type": scan_type,
            "image_findings": findings,
            "message": (
                "Image analyzed successfully."
                if findings.get("success")
                else "Image uploaded. Analysis result may be limited."
            ),
        }


@app.post("/chat/skip-stage")
@limiter.limit("20/minute")
async def skip_stage(
    request: Request,
    data: ChatStructuredInput
):
    """User skips an optional stage (Medications, Reports, Imaging)."""
    state = conversation_manager.get_conversation(data.conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")

    skip_map = {
        "medications": "medications_skipped",
        "reports": "reports_skipped",
        "imaging": "imaging_skipped",
    }
    flag = skip_map.get(data.stage)
    if flag:
        conversation_manager.update_collected_data(data.conversation_id, flag, True)

    result = intake_engine.process_structured_input(
        conversation_id=data.conversation_id,
        stage=data.stage,
        data={**data.data, f"{data.stage}_skipped": True}
    )

    if result["trigger_analysis"]:
        return await _run_council_analysis(data.conversation_id, state)

    return {
        "success": True,
        "message": result["response"],
        "stage": result["stage"],
        "stage_metadata": result["stage_metadata"],
    }


@app.get("/chat/{conversation_id}/history")
@limiter.limit("20/minute")
def get_chat_history(
    request: Request,
    conversation_id: str
):
    state = conversation_manager.get_conversation(conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "success": True,
        "conversation_id": conversation_id,
        "stage": state.stage.value,
        "imaging_needed": state.imaging_needed,
        "imaging_types": state.imaging_types,
        "messages": [m.dict() for m in state.messages],
        "collected_data": state.collected_data,
    }


# ── Internal: run the 3-model council and format results ──

async def _run_council_analysis(conversation_id: str, state, selected_model: str = None) -> dict:
    """Runs analysis — full council or a single model — and returns structured results."""
    SINGLE_MODEL_KEYS = {"medgemma", "openbiollm", "mistral"}
    use_single = selected_model and selected_model.lower() in SINGLE_MODEL_KEYS

    payload = conversation_manager.build_analysis_payload(conversation_id)
    conversation_manager.update_stage(conversation_id, IntakeStage.ANALYZING)

        from utils.runpod_client import RunpodClient
        rpc = RunpodClient()

        if rpc.is_configured:
            print("[Chat] ☁️ Active RunPod credentials detected. Forwarding to Cloud GPU...")
            
            # Pack exactly what RunPod's preprocessor expects
            runpod_payload = {
                "patient_id": payload.get("patient_id", conversation_id),
                "symptoms_text": payload.get("symptoms_text", ""),
                "medical_history_text": payload.get("medical_history_text") or payload.get("prior_diagnosis", ""),
                "lab_text": payload.get("lab_text", ""),
                "medications_text": payload.get("medications_text", ""),
                "age": payload.get("age"),
                "gender": payload.get("gender")
            }
            
            # Send to RunPod Serverless GPU
            rp_result = await rpc.run_council_analysis(
                patient_state=runpod_payload,
                mode="single" if use_single else "council",
                model_key=selected_model.lower() if use_single else None
            )
            
            # Extract standard dicts from RunPod JSON response
            patient_state_dict = rp_result.get("patient_state", {})
            clinical_output_dict = rp_result.get("clinical_analysis", {})
            confidence_report_dict = rp_result.get("confidence_report", {})
            
            # We still need active data gaps locally for the chat UI missing data chips
            data_gaps = uncertainty_engine.generate_active_data_gaps(
                patient_state_dict, clinical_output_dict
            )

        else:
            print("[Chat] 💻 No RunPod credentials found. Running AI Council locally...")
            import asyncio
            
            patient_state = preprocessor.process(
                patient_id=payload.get("patient_id", conversation_id),
                symptoms_text=payload.get("symptoms_text", ""),
                medical_history_text=payload.get("medical_history_text") or payload.get("prior_diagnosis", ""),
                lab_text=payload.get("lab_text", ""),
                medications_text=payload.get("medications_text", ""),
                age=payload.get("age"),
                gender=payload.get("gender")
            )
            patient_state_dict = patient_state.dict()

            # ── Route to single model or full council ──
            if use_single:
                clinical_output = await asyncio.to_thread(reasoner.analyze_single, patient_state_dict, selected_model.lower())
            else:
                clinical_output = await asyncio.to_thread(reasoner.analyze, patient_state_dict)
            clinical_output_dict = clinical_output.dict()

            confidence_report = uncertainty_engine.analyze_clinical_confidence(
                patient_state_dict, clinical_output_dict
            )
            confidence_report_dict = confidence_report.dict()

            data_gaps = uncertainty_engine.generate_active_data_gaps(
                patient_state_dict, clinical_output_dict
            )

        # ── Regardless of Cloud vs Local, format message and update Audit Logs ──
        result_message = _format_analysis_for_chat(
            clinical_output_dict, confidence_report_dict, data_gaps
        )

        conversation_manager.set_analysis_result(conversation_id, clinical_output_dict)
        conversation_manager.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=result_message
        )

        chat_patient_id = state.patient_id or conversation_id
        log_result = audit_logger.log_prediction(
            patient_id=chat_patient_id,
            patient_state=patient_state_dict,
            clinical_analysis=clinical_output_dict,
            doctor_id=None
        )
        twin_engine.record_visit(
            patient_state=patient_state_dict,
            clinical_analysis=clinical_output_dict,
            audit_log_id=log_result.get("log_id", "unknown")
        )

        return {
            "success": True,
            "message": result_message,
            "stage": "results",
            "stage_metadata": intake_engine.get_stage_metadata(IntakeStage.RESULTS),
            "analysis": clinical_output.dict(),
            "confidence": confidence_report.dict(),
            "data_gaps": data_gaps,
            "audit_log_id": log_result.get("log_id"),
            "imaging_used": len(state.images_uploaded) > 0,
            "reports_used": len(state.reports_uploaded) > 0,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": "I encountered an issue analyzing your data. Please try again.",
            "stage": "analyzing",
            "stage_metadata": intake_engine.get_stage_metadata(IntakeStage.ANALYZING),
            "error": str(e)
        }



@app.post("/v1/chat/completions")
@limiter.limit("30/minute")
async def chat_completions(
    request: Request,
    data: ChatCompletionRequest
):
    # This endpoint mimics the OpenAI /v1/chat/completions structure
    # extract the last user message
    user_message = next((m.content for m in reversed(data.messages) if m.role == "user"), None)
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    conv_id = "openai_compat"
    if not conversation_manager.get_conversation(conv_id):
        state = conversation_manager.create_conversation()
        del conversation_manager._conversations[state.conversation_id]
        state.conversation_id = conv_id
        conversation_manager._conversations[conv_id] = state

    response_text = intake_engine.process_message(
        conversation_id=conv_id,
        user_message=user_message
    )

    if response_text == "__TRIGGER_ANALYSIS__":
        state = conversation_manager.get_conversation(conv_id)
        if hasattr(state, "collected_data"):
            collected = state.collected_data
        else:
            collected = {}
            
        try:
            patient_state = preprocessor.process(
                patient_id=state.patient_id or conv_id,
                symptoms_text=collected.get("symptoms_text", ""),
                medical_history_text=collected.get("medical_history_text", ""),
                lab_text=collected.get("lab_text", ""),
                medications_text=collected.get("medications_text", ""),
                age=collected.get("age"),
                gender=collected.get("gender")
            )

            import asyncio
            clinical_output = await asyncio.to_thread(reasoner.analyze, patient_state.dict())
            confidence_report = uncertainty_engine.analyze_clinical_confidence(
                patient_state.dict(), clinical_output.dict()
            )
            data_gaps = uncertainty_engine.generate_active_data_gaps(
                patient_state.dict(), clinical_output.dict()
            )
            response_text = _format_analysis_for_chat(
                clinical_output.dict(), confidence_report.dict(), data_gaps
            )
            
            # Reset the mock conversation so it's fresh for the next intake
            del conversation_manager._conversations[conv_id]
            
        except Exception as e:
            response_text = f"I encountered an issue analyzing your data: {str(e)}"

    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": int(__import__("time").time()),
        "model": data.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message),
            "completion_tokens": len(response_text),
            "total_tokens": len(user_message) + len(response_text)
        }
    }


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _format_analysis_for_chat(clinical: dict, confidence: dict, data_gaps: list) -> str:
    conditions       = clinical.get("top_3_conditions", [])
    confidence_level = confidence.get("confidence_level", "LOW")
    overall          = confidence.get("overall_confidence", 0)
    summary          = clinical.get("reasoning_summary", "")

    emoji_map = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🟠", "CRITICAL_LOW": "🔴"}
    emoji = emoji_map.get(confidence_level, "🟡")

    msg  = f"## 🩺 Curezy AI Health Assessment\n\n"
    msg += f"**Confidence:** {emoji} {confidence_level} ({overall}%)\n\n"
    msg += f"---\n\n### 📋 Possible Conditions\n\n"

    for i, cond in enumerate(conditions, 1):
        name      = cond.get("condition", "Unknown")
        prob      = cond.get("probability", 0)
        reasoning = cond.get("reasoning", "")
        msg += f"**{i}. {name}** — {prob}% likelihood\n"
        msg += f"_{reasoning}_\n\n"

    msg += f"---\n\n### 💡 Summary\n{summary}\n\n"

    if data_gaps:
        msg += f"---\n\n### 🔬 Recommended Next Steps\n"
        for gap in data_gaps:
            msg += f"- {gap}\n"

    if confidence.get("uncertainty_warning"):
        msg += f"\n\n⚠️ _{confidence['uncertainty_warning']}_"

    msg += f"\n\n---\n_This is an AI assessment, not a medical diagnosis. Please consult a qualified doctor._"
    return msg


# ─────────────────────────────────────────
# FINE-TUNING PIPELINE ROUTES
# ─────────────────────────────────────────

FINETUNE_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "finetune", "uploads")
os.makedirs(FINETUNE_UPLOAD_DIR, exist_ok=True)

ALLOWED_FINETUNE_EXT = {".pdf", ".txt", ".csv", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


@app.post("/finetune/upload")
@limiter.limit("5/minute")
async def finetune_upload(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload dataset file and start automated fine-tuning pipeline.
    Supported: PDF, TXT, CSV, DOCX, PNG, JPG, JPEG, TIFF, BMP
    Returns job_id for polling /finetune/status/{job_id}
    """
    import re as _re
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_FINETUNE_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported: {ext}. Allowed: {', '.join(ALLOWED_FINETUNE_EXT)}"
        )

    safe_name = _re.sub(r"[^\w\-_.]", "_", file.filename or "upload")[:100]
    save_path = os.path.join(FINETUNE_UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    job_id = start_pipeline(file_path=save_path, file_name=file.filename or safe_name)

    return {
        "success":   True,
        "job_id":    job_id,
        "file_name": file.filename,
        "file_size": len(content),
        "status":    "started",
        "message":   f"Pipeline started. Poll /finetune/status/{job_id} for updates."
    }


@app.get("/finetune/status/{job_id}")
@limiter.limit("60/minute")
def finetune_status(request: Request, job_id: str):
    """Poll the real-time status of a fine-tuning job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"success": True, "job": job}



@app.get("/finetune/jobs")
@limiter.limit("20/minute")
def finetune_jobs(request: Request):
    """List all fine-tuning jobs (most recent first)."""
    jobs = list_jobs()
    return {"success": True, "count": len(jobs), "jobs": jobs}


@app.post("/finetune/rollback")
@limiter.limit("5/minute")
def finetune_rollback(request: Request):
    """Rollback clinical_reasoner.py to original (pre-finetune) models."""
    deployer = OllamaDeploy()
    success = deployer.rollback()
    return {
        "success": success,
        "message": "Rolled back to original models" if success else "No backup found"
    }


# ══════════════════════════════════════════════════════════════
# BENCHMARK ENDPOINTS
# ══════════════════════════════════════════════════════════════

import subprocess
import threading
import json as _json
import sys as _sys

_bench_proc = {"proc": None, "mode": None, "started_at": None, "job_id": None}
_bench_lock = threading.Lock()

class BenchmarkRunRequest(BaseModel):
    mode: str = "quick"  # "quick" or "full"

@app.post("/benchmark/run")
@limiter.limit("3/minute")
def benchmark_run(request: Request, body: BenchmarkRunRequest):
    """Start the council benchmark in a background subprocess."""
    import datetime, uuid
    with _bench_lock:
        p = _bench_proc.get("proc")
        if p and p.poll() is None:
            return {"success": False, "message": "Benchmark already running", "job_id": _bench_proc.get("job_id")}
        script = os.path.join(os.path.dirname(__file__), "training", "real_benchmark.py")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"  # force UTF-8 in subprocess
        env["PYTHONUNBUFFERED"] = "1"       # force unbuffered output
        proc = subprocess.Popen(
            [_sys.executable, "-u", script, "--mode", body.mode],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=os.path.dirname(__file__), env=env
        )
        job_id = str(uuid.uuid4())[:8]
        _bench_proc["proc"]       = proc
        _bench_proc["mode"]       = body.mode
        _bench_proc["started_at"] = datetime.datetime.now().isoformat()
        _bench_proc["job_id"]     = job_id
        _bench_proc["lines"]      = []

        def _stream():
            for line in proc.stdout:
                stripped = line.rstrip()
                _bench_proc["lines"].append(stripped)
                print(f"[BENCH] {stripped}", flush=True)  # echo to uvicorn terminal

        threading.Thread(target=_stream, daemon=True).start()

    return {"success": True, "job_id": job_id, "mode": body.mode, "message": f"Benchmark started ({body.mode} mode)"}


@app.get("/benchmark/status")
@limiter.limit("60/minute")
def benchmark_status(request: Request):
    """Live benchmark status: running/done + recent output lines."""
    with _bench_lock:
        proc       = _bench_proc.get("proc")
        running    = proc is not None and proc.poll() is None
        exit_code  = proc.poll() if proc else None
        lines      = list(_bench_proc.get("lines", []))[-60:]  # last 60 lines
        started_at = _bench_proc.get("started_at")
        job_id     = _bench_proc.get("job_id")
        mode       = _bench_proc.get("mode")

    # Parse live stats from output lines
    current_q = ""
    council_score = None
    for line in reversed(lines):
        if not current_q and ("[Q" in line or "[Round" in line):
            current_q = line.strip()
        if "COUNCIL SCORE:" in line:
            try:
                council_score = float(line.split("COUNCIL SCORE:")[1].split("%")[0].strip())
            except Exception:
                pass
        if current_q and council_score is not None:
            break

    status = "running" if running else ("completed" if exit_code == 0 else ("idle" if proc is None else "failed"))

    return {
        "job_id":        job_id,
        "status":        status,
        "mode":          mode,
        "started_at":    started_at,
        "current_step":  current_q,
        "council_score": council_score,
        "output_lines":  lines,
        "exit_code":     exit_code,
    }


@app.get("/benchmark/results")
@limiter.limit("30/minute")
def benchmark_results(request: Request):
    """Return the most recent benchmark_results.json (if it exists)."""
    path = os.path.join(os.path.dirname(__file__), "training", "benchmark_results.json")
    # Also check root ai-service dir (where script is run from sometimes)
    alt  = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    for p in [path, alt]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = _json.load(f)
            return {"success": True, "results": data}
    return {"success": False, "message": "No benchmark results yet — run a benchmark first"}


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — COUNCIL FEEDBACK ENDPOINT
# Records patient/doctor ratings for the auto-training loop.
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/feedback/council")
@limiter.limit("60/minute")
async def submit_council_feedback(request: Request, data: CouncilFeedbackInput):
    """
    Receive star ratings + optional doctor corrections from the FeedbackBar UI.
    Updates the council_outcomes row for this session in Supabase.
    If rating == 5 or doctor_verified == true, auto-promotes the case to case_library.
    """
    import datetime

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not (supabase_url and supabase_key):
        # Supabase not configured — accept gracefully so UI doesn't error
        return {"success": True, "message": "Feedback noted (persistence not configured)"}

    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)

        # 1. Update the matching council_outcomes row
        update_payload = {
            "user_rating":          data.rating,
            "doctor_verified":      data.doctor_verified or False,
            "feedback_notes":       data.feedback_notes or "",
            "feedback_timestamp":   datetime.datetime.utcnow().isoformat(),
        }
        if data.actual_diagnosis:
            update_payload["actual_diagnosis"] = data.actual_diagnosis.strip()

        res = client.table("council_outcomes") \
            .update(update_payload) \
            .eq("session_id", data.session_id) \
            .execute()

        # 2. Auto-promote to case_library if high quality
        should_promote = (data.rating == 5) or (data.doctor_verified is True)
        if should_promote and res.data:
            outcome = res.data[0]
            all_conds = outcome.get("all_conditions", [])
            top_cond  = all_conds[0] if all_conds else {}

            if top_cond.get("condition") and outcome.get("soap_note"):
                quality_source = "doctor_verified" if data.doctor_verified else "user_5star"
                client.table("case_library").insert({
                    "outcome_id":       outcome.get("id"),
                    "soap_note":        outcome.get("soap_note", ""),
                    "symptoms":         outcome.get("symptoms", []),
                    "top_condition":    data.actual_diagnosis or top_cond.get("condition"),
                    "probability":      top_cond.get("probability", 60),
                    "evidence":         top_cond.get("evidence", []),
                    "reasoning":        top_cond.get("reasoning", ""),
                    "reasoning_summary":outcome.get("reasoning_summary", ""),
                    "quality_source":   quality_source,
                    "q_score":          outcome.get("q_score"),
                    "user_rating":      data.rating,
                }).execute()
                print(f"[Feedback] 📚 Case promoted to library (source: {quality_source})")

        return {
            "success":  True,
            "message":  "Thank you for your feedback!",
            "promoted": should_promote,
        }

    except Exception as e:
        print(f"[Feedback] ❌ Error: {e}")
        # Don't crash the UI — return gracefully
        return {"success": True, "message": "Feedback recorded"}

