"""
runpod_handler.py
=================
RunPod Serverless handler for Curezy AURANET.

How it works:
  - On cold start: Ollama server launches, models load into VRAM
  - On each request: handler() runs the council/single-model analysis
  - When idle (no requests): RunPod scales workers to 0 → GPU stops → $0 cost
  - On next request: pod spins back up (cold start ~30–60s)

Build & deploy:
  docker build -t your-dockerhub/curezy-auranet:latest .
  docker push your-dockerhub/curezy-auranet:latest
  → Register image in RunPod Serverless dashboard
"""

import runpod
import subprocess
import time
import os
import sys

# ── Add the ai-service root to the path ───────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── Start Ollama on cold start (runs once per worker lifetime) ─────────────────
def _start_ollama():
    print("[Curezy] Starting Ollama server...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait for Ollama to be ready
    for _ in range(30):
        try:
            import ollama as _ol
            _ol.list()
            print("[Curezy] ✅ Ollama ready")
            break
        except Exception:
            time.sleep(2)
    else:
        raise RuntimeError("Ollama failed to start within 60s")

    # Pull models if not already cached (first cold start on new worker)
    _pull_if_needed("alibayram/medgemma:4b")
    _pull_if_needed("koesn/llama3-openbiollm-8b:latest")
    _pull_if_needed("mistral:7b")

    # Brand models (idempotent — skips if already branded)
    print("[Curezy] Applying Curezy brand names...")
    try:
        import subprocess as sp
        sp.run(["python", "ollama_rename.py"], check=False)
    except Exception as e:
        print(f"[Curezy] rename warning: {e}")
    print("[Curezy] ✅ Curezy AURIX + AURA + AURIS ready")


def _pull_if_needed(model: str):
    import ollama as _ol
    try:
        models = _ol.list()
        names = [m.model for m in models.get("models", [])]
        if not any(model.split(":")[0] in n for n in names):
            print(f"[Curezy] Pulling {model} (first start)...")
            _ol.pull(model)
        else:
            print(f"[Curezy] ✅ {model} already cached")
    except Exception as e:
        print(f"[Curezy] Pull error for {model}: {e}")

_start_ollama()

# ── Load services (once per worker) ───────────────────────────────────────────
print("[Curezy] Loading Curezy AURANET council...")
from preprocessing.patient_preprocessor import PatientPreprocessor
from agents.clinical_reasoner import ClinicalReasoner
from confidence.uncertainty_engine import UncertaintyEngine
import asyncio

preprocessor      = PatientPreprocessor()
reasoner          = ClinicalReasoner()
uncertainty_engine = UncertaintyEngine()

print("[Curezy] ✅ Council ready — Curezy AURIX + AURA + AURIS loaded")


# ── Main handler ──────────────────────────────────────────────────────────────

def handler(job: dict) -> dict:
    """
    RunPod calls this function for every incoming request.

    Expected input format:
    {
        "input": {
            "mode": "council",           # "council" | "single"
            "model_key": "medgemma",     # only needed for mode=single
            "patient_id": "p_001",
            "symptoms_text": "...",
            "medical_history_text": "",
            "lab_text": "",
            "medications_text": "",
            "age": 35,
            "gender": "male"
        }
    }
    """
    try:
        inp = job.get("input", {})
        mode      = inp.get("mode", "council")
        model_key = inp.get("model_key", None)

        # Build patient state
        patient_state = preprocessor.process(
            patient_id            = inp.get("patient_id", "runpod_patient"),
            symptoms_text         = inp.get("symptoms_text", ""),
            medical_history_text  = inp.get("medical_history_text", ""),
            lab_text              = inp.get("lab_text", ""),
            medications_text      = inp.get("medications_text", ""),
            age                   = inp.get("age", None),
            gender                = inp.get("gender", None),
        )

        # Run analysis
        if mode == "single" and model_key:
            clinical_output = reasoner.analyze_single(patient_state.dict(), model_key)
        else:
            clinical_output = asyncio.run(reasoner.analyze(patient_state.dict()))

        # Confidence report
        confidence_report = uncertainty_engine.analyze_clinical_confidence(
            patient_state.dict(), clinical_output.dict()
        )

        return {
            "success":          True,
            "mode":             mode,
            "patient_state":    patient_state.dict(),
            "clinical_analysis": clinical_output.dict(),
            "confidence_report": confidence_report.dict(),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error":   str(e),
        }


# ── Start RunPod worker ───────────────────────────────────────────────────────
runpod.serverless.start({"handler": handler})
