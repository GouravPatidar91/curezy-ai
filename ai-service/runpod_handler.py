"""
runpod_handler.py  —  Curezy AURANET Serverless Entry Point
Models and services are loaded lazily on first request to avoid startup timeouts.
"""

import runpod
import subprocess
import time
import sys
import os
import traceback

# ── Add ai-service root to path ───────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Lazy globals (loaded on first request) ────────────────────────────────────
_initialized    = False
_preprocessor   = None
_reasoner       = None
_uncertainty    = None
_xray_analyzer  = None


def _init():
    """Cold-start init — runs once per worker on the first request."""
    global _initialized, _preprocessor, _reasoner, _uncertainty

    if _initialized:
        return

    print("[Curezy] Cold start — initialising worker...")

    # 1. Start Ollama
    _start_ollama()

    # 2. Pull + brand models (skipped if already cached via Network Volume)
    _pull_if_needed("alibayram/medgemma:4b")
    _pull_if_needed("koesn/llama3-openbiollm-8b:latest")
    _pull_if_needed("mistral:7b")
    _rename_models()

    # 3. Import heavy modules (after Ollama is ready)
    print("[Curezy] Loading Python services...")
    try:
        from preprocessing.patient_preprocessor import PatientPreprocessor
        from agents.clinical_reasoner import ClinicalReasoner
        from confidence.uncertainty_engine import UncertaintyEngine
        from imaging.xray_analyzer import ChestXRayAnalyzer

        _preprocessor   = PatientPreprocessor()
        _reasoner       = ClinicalReasoner()
        _uncertainty    = UncertaintyEngine()
        _xray_analyzer  = ChestXRayAnalyzer()
        print("[Curezy] ✅ All services loaded")
    except Exception as e:
        print(f"[Curezy] ❌ Service load error: {e}")
        traceback.print_exc()
        raise

    _initialized = True
    print("[Curezy] ✅ Worker ready!")


def _start_ollama():
    print("[Curezy] Starting Ollama...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    for i in range(30):
        try:
            import ollama as _ol
            _ol.list()
            print("[Curezy] ✅ Ollama running")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Ollama did not start within 60s")


def _pull_if_needed(model: str):
    try:
        import ollama as _ol
        result = _ol.list()
        # Handle both dict and object responses
        models_list = result.get("models", []) if isinstance(result, dict) else getattr(result, "models", [])
        names = []
        for m in models_list:
            name = m.get("model", "") if isinstance(m, dict) else getattr(m, "model", "")
            names.append(name)

        base = model.split(":")[0]
        if not any(base in n for n in names):
            print(f"[Curezy] Pulling {model}...")
            _ol.pull(model)
            print(f"[Curezy] ✅ {model} pulled")
        else:
            print(f"[Curezy] ✅ {model} already cached")
    except Exception as e:
        print(f"[Curezy] ⚠️ Pull warning for {model}: {e}")


def _rename_models():
    try:
        script = os.path.join(os.path.dirname(__file__), "ollama_rename.py")
        if os.path.exists(script):
            subprocess.run([sys.executable, script], timeout=60, check=False)
            print("[Curezy] ✅ Models branded")
    except Exception as e:
        print(f"[Curezy] ⚠️ Rename warning: {e}")


# ── Main handler ──────────────────────────────────────────────────────────────

def handler(job: dict) -> dict:
    """
    RunPod calls this for every request.

    Input format:
    {
        "input": {
            "mode": "council",        # or "single"
            "model_key": "medgemma",  # only for mode=single
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
        # Lazy init on first request
        _init()

        inp       = job.get("input", {})
        mode      = inp.get("mode", "council")
        model_key = inp.get("model_key", None)

        if mode == "xray":
            print("[Curezy] Running X-ray analysis...")
            image_b64 = inp.get("image_base64")
            if not image_b64:
                return {"success": False, "error": "No image_base64 provided for mode=xray"}
            
            # Save temp image
            import base64
            os.makedirs(".tmp", exist_ok=True)
            temp_path = os.path.join(".tmp", f"runpod_xray_{int(time.time())}.png")
            with open(temp_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
            
            try:
                result = _xray_analyzer.analyze(temp_path)
                return result
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # Standard clinical analysis
        patient_state = _preprocessor.process(
            patient_id           = inp.get("patient_id", "runpod_patient"),
            symptoms_text        = inp.get("symptoms_text", ""),
            medical_history_text = inp.get("medical_history_text", ""),
            lab_text             = inp.get("lab_text", ""),
            medications_text     = inp.get("medications_text", ""),
            age                  = inp.get("age", None),
            gender               = inp.get("gender", None),
        )

        import threading
        def _run_in_thread(data, result_box, error_box):
            try:
                if mode == "single" and model_key:
                    result_box.append(_reasoner.analyze_single(data, model_key))
                else:
                    result_box.append(_reasoner.analyze(data))
            except Exception as ex:
                import traceback
                traceback.print_exc()
                error_box.append(ex)

        res = []
        errs = []
        t = threading.Thread(target=_run_in_thread, args=(patient_state.dict(), res, errs))
        t.start()
        t.join()

        if errs:
            raise errs[0]
        if not res:
            raise RuntimeError("Reasoner returned no result and no error")
            
        clinical_output = res[0]

        confidence_report = _uncertainty.analyze_clinical_confidence(
            patient_state.dict(), clinical_output.dict()
        )

        return {
            "success":           True,
            "mode":              mode,
            "patient_state":     patient_state.dict(),
            "clinical_analysis": clinical_output.dict(),
            "confidence_report": confidence_report.dict(),
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error":   str(e),
            "trace":   traceback.format_exc(),
        }


# ── Start RunPod worker ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[Curezy] Starting RunPod serverless worker...")
    runpod.serverless.start({"handler": handler})
