"""
finetune/pipeline.py
=====================
Orchestrates the full automated fine-tuning pipeline:
  1. Parse file (PDF/TXT/CSV/DOCX/Image)
  2. Convert to training JSONL (via Groq AI)
  3. Quality filter
  4. Fine-tune all 3 models (Unsloth LoRA)
  5. Deploy to Ollama

Job status is stored in a shared in-memory dict for polling via API.
"""

import os
import json
import time
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional

from finetune.parser import parse_file
from finetune.converter import JSOLConverter
from finetune.quality_filter import QualityFilter
from finetune.trainer import ModelTrainer
from finetune.deploy import OllamaDeploy

# ─────────────────────────────────────────────
# Shared job store (in-memory, keyed by job_id)
# ─────────────────────────────────────────────
_job_store: dict = {}
_lock = threading.Lock()

DATASET_DIR = Path(__file__).parent / "datasets"
UPLOAD_DIR  = Path(__file__).parent / "uploads"


def get_job(job_id: str) -> Optional[dict]:
    with _lock:
        return _job_store.get(job_id)


def list_jobs() -> list:
    with _lock:
        return sorted(_job_store.values(), key=lambda j: j.get("created_at", ""), reverse=True)


def _update_job(job_id: str, **kwargs):
    with _lock:
        if job_id in _job_store:
            _job_store[job_id].update(kwargs)
            _job_store[job_id]["updated_at"] = datetime.now().isoformat()


# ─────────────────────────────────────────────
# Pipeline runner (runs in background thread)
# ─────────────────────────────────────────────

def run_pipeline(file_path: str, file_type: str, job_id: str):
    """
    Full pipeline. Runs in a background thread.
    Updates job_store throughout for real-time status polling.
    """
    def progress(msg: str, pct: int):
        print(f"[Pipeline:{job_id}] {pct}% — {msg}")
        _update_job(job_id, status="running", stage_message=msg, progress=pct)

    _update_job(job_id, status="running", stage="parsing", progress=2)

    try:
        # ── Step 1: Parse File ─────────────────────────────────────────
        progress("📄 Parsing file...", 5)
        _update_job(job_id, stage="parsing")

        parse_result = parse_file(file_path)
        raw_text = parse_result["text"]
        char_count = parse_result["char_count"]

        if char_count < 100:
            raise ValueError(f"Extracted text too short ({char_count} chars). Is the file readable?")

        _update_job(job_id, parse_stats={
            "source_type": parse_result["source_type"],
            "char_count":  char_count,
            "file_name":   parse_result["file_name"]
        })
        progress(f"✅ Parsed {char_count:,} characters from {file_type.upper()}", 15)

        # ── Step 2: Convert to JSONL ───────────────────────────────────
        progress("🤖 Converting to training data via AI...", 20)
        _update_job(job_id, stage="converting")

        converter = JSOLConverter()
        raw_examples = converter.convert(raw_text, job_id)

        if not raw_examples:
            raise ValueError("AI converter produced 0 examples. Check if file has valid medical content.")

        progress(f"✅ Generated {len(raw_examples)} raw examples", 40)
        _update_job(job_id, raw_example_count=len(raw_examples))

        # ── Step 3: Quality Filter ─────────────────────────────────────
        progress("✅ Running quality filter...", 45)
        _update_job(job_id, stage="filtering")

        qfilter = QualityFilter(use_llm_scoring=True)
        filtered, filter_stats = qfilter.filter(raw_examples)

        if not filtered:
            raise ValueError("All examples failed quality filter. Try a file with more detailed medical content.")

        # Save filtered dataset to JSONL
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        jsonl_path = str(DATASET_DIR / f"{job_id}_dataset.jsonl")
        converter.save_jsonl(filtered, jsonl_path)

        progress(f"✅ {len(filtered)} high-quality examples saved (filtered {len(raw_examples) - len(filtered)} low-quality)", 55)
        _update_job(job_id, filter_stats=filter_stats, dataset_path=jsonl_path)

        # ── Step 4: Fine-Tune All Models ───────────────────────────────
        progress("🔥 Starting fine-tuning (this may take 30-90 minutes)...", 60)
        _update_job(job_id, stage="training")

        def train_progress(msg, pct):
            progress(msg, pct)

        trainer = ModelTrainer(progress_callback=train_progress)
        train_results = trainer.train_all(jsonl_path, job_id)

        successful_models = [name for name, r in train_results.items() if r.get("success")]
        failed_models = [name for name, r in train_results.items() if not r.get("success")]

        if not successful_models:
            raise ValueError(f"All models failed training: {[r.get('error') for r in train_results.values()]}")

        progress(f"✅ Trained: {', '.join(successful_models)}", 82)
        if failed_models:
            progress(f"⚠️  Failed: {', '.join(failed_models)} (partial success)", 82)

        _update_job(job_id, train_results=train_results)

        # ── Step 5: Deploy to Ollama ───────────────────────────────────
        progress("🚀 Deploying to Ollama...", 85)
        _update_job(job_id, stage="deploying")

        deployer = OllamaDeploy(progress_callback=train_progress)
        deploy_results = deployer.deploy_all(train_results)

        deployed_names = [
            r.get("model_name") for r in deploy_results.values()
            if r.get("success")
        ]

        progress(f"✅ Deployed: {', '.join(deployed_names)}", 98)
        _update_job(job_id, deploy_results=deploy_results)

        # ── Complete ───────────────────────────────────────────────────
        _update_job(
            job_id,
            status="completed",
            stage="done",
            progress=100,
            stage_message=f"✅ Pipeline complete! {len(deployed_names)} model(s) deployed.",
            completed_at=datetime.now().isoformat(),
            summary={
                "characters_parsed":   char_count,
                "raw_examples":        len(raw_examples),
                "filtered_examples":   len(filtered),
                "models_trained":      successful_models,
                "models_deployed":     deployed_names,
                "models_failed":       failed_models,
            }
        )
        print(f"\n[Pipeline:{job_id}] ✅ COMPLETE — {len(deployed_names)} models deployed")

    except Exception as e:
        print(f"\n[Pipeline:{job_id}] ❌ FAILED: {e}")
        traceback.print_exc()
        _update_job(
            job_id,
            status="failed",
            stage="error",
            progress=0,
            error=str(e),
            stage_message=f"❌ Error: {str(e)[:200]}",
            failed_at=datetime.now().isoformat()
        )


def start_pipeline(file_path: str, file_name: str) -> str:
    """
    Create a new job and start the pipeline in a background thread.
    Returns the job_id.
    """
    import uuid
    job_id = f"ft_{uuid.uuid4().hex[:10]}"
    file_ext = Path(file_name).suffix.lower().lstrip(".")

    with _lock:
        _job_store[job_id] = {
            "job_id":     job_id,
            "file_name":  file_name,
            "file_type":  file_ext,
            "status":     "queued",
            "stage":      "queued",
            "progress":   0,
            "stage_message": "Queued...",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "error":      None,
            "summary":    None
        }

    t = threading.Thread(
        target=run_pipeline,
        args=(file_path, file_ext, job_id),
        daemon=True
    )
    t.start()
    print(f"[Pipeline] Started job {job_id} for {file_name}")
    return job_id
