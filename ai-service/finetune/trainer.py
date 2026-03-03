"""
finetune/trainer.py
====================
Unsloth LoRA fine-tuner for the 3 Curezy council models.
Trains each model on the filtered JSONL dataset using 4-bit QLoRA.

Requirements: unsloth, trl, transformers, datasets (CUDA required)
"""

import os
import json
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Callable

# ─────────────────────────────────────────────
# HuggingFace model mappings for each Ollama model
# ─────────────────────────────────────────────
OLLAMA_TO_HF = {
    "alibayram/medgemma:4b":              "google/gemma-3-4b-it",
    "koesn/llama3-openbiollm-8b:latest": "aaditya/Llama3-OpenBioLLM-8B",
    "mistral:7b":                         "mistralai/Mistral-7B-Instruct-v0.3",
}

ADAPTER_DIR    = Path(__file__).parent / "adapters"
GGUF_DIR       = Path(__file__).parent / "gguf"
DATASET_DIR    = Path(__file__).parent / "datasets"

# Training hyperparameters
LORA_CONFIG = {
    "r":                16,
    "lora_alpha":       32,
    "lora_dropout":     0.05,
    "target_modules":   ["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
    "bias":             "none",
}

TRAIN_CONFIG = {
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,
    "num_train_epochs":            3,
    "learning_rate":               2e-4,
    "max_seq_length":              2048,
    "warmup_steps":                10,
    "save_steps":                  50,
    "logging_steps":               10,
    "optim":                       "adamw_8bit",
    "lr_scheduler_type":           "cosine",
    "fp16":                        False,
    "bf16":                        True,
}


class ModelTrainer:

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_cb = progress_callback or (lambda msg, pct: None)
        ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
        GGUF_DIR.mkdir(parents=True, exist_ok=True)

    def train_all(self, jsonl_path: str, job_id: str) -> Dict:
        """
        Fine-tune all 3 council models on the same dataset.
        Returns dict of results per model.
        """
        from agents.clinical_reasoner import COUNCIL

        results = {}
        for i, doctor in enumerate(COUNCIL):
            model_name = doctor["name"]
            ollama_model = doctor["model"]
            hf_model = OLLAMA_TO_HF.get(ollama_model)

            if not hf_model:
                results[model_name] = {"success": False, "error": f"No HF mapping for {ollama_model}"}
                continue

            pct_base = int(i / len(COUNCIL) * 80)
            self.progress_cb(f"Training {model_name}...", pct_base + 5)

            try:
                adapter_path = self._train_model(
                    hf_model_id=hf_model,
                    doctor_name=model_name,
                    jsonl_path=jsonl_path,
                    job_id=job_id,
                    progress_offset=pct_base
                )
                gguf_path = self._export_gguf(adapter_path, model_name, hf_model)
                results[model_name] = {
                    "success":      True,
                    "adapter_path": str(adapter_path),
                    "gguf_path":    str(gguf_path),
                    "hf_model":     hf_model
                }
                self.progress_cb(f"✅ {model_name} trained", pct_base + 25)
            except Exception as e:
                print(f"[Trainer] ❌ {model_name} failed: {e}")
                results[model_name] = {"success": False, "error": str(e)}

        return results

    def _train_model(self, hf_model_id: str, doctor_name: str,
                     jsonl_path: str, job_id: str, progress_offset: int = 0) -> Path:
        """Train a single model with Unsloth LoRA. Returns adapter path."""
        try:
            from unsloth import FastLanguageModel
            from trl import SFTTrainer, SFTConfig
            from datasets import Dataset
            import torch
        except ImportError as e:
            raise ImportError(f"Missing dependency: {e}. Run: pip install unsloth trl datasets")

        print(f"\n[Trainer] Loading {hf_model_id} with Unsloth...")
        self.progress_cb(f"Loading {doctor_name} base model...", progress_offset + 5)

        # Load with 4-bit quantization
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name     = hf_model_id,
            max_seq_length = TRAIN_CONFIG["max_seq_length"],
            dtype          = None,  # Auto-detect
            load_in_4bit   = True,
        )

        # Apply LoRA
        model = FastLanguageModel.get_peft_model(
            model,
            r              = LORA_CONFIG["r"],
            target_modules = LORA_CONFIG["target_modules"],
            lora_alpha     = LORA_CONFIG["lora_alpha"],
            lora_dropout   = LORA_CONFIG["lora_dropout"],
            bias           = LORA_CONFIG["bias"],
            use_gradient_checkpointing = "unsloth",
            random_state   = 42,
        )

        # Load dataset
        print(f"[Trainer] Loading dataset from {jsonl_path}")
        examples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    ex = json.loads(line)
                    # Format as Alpaca prompt
                    text = self._format_alpaca(ex, tokenizer)
                    examples.append({"text": text})

        if not examples:
            raise ValueError("Dataset is empty after loading")

        dataset = Dataset.from_list(examples)
        print(f"[Trainer] Dataset: {len(dataset)} examples")
        self.progress_cb(f"Training {doctor_name} on {len(dataset)} examples...", progress_offset + 15)

        # Train
        adapter_path = ADAPTER_DIR / f"{doctor_name.replace(' ', '_').lower()}_{job_id}"
        
        trainer = SFTTrainer(
            model      = model,
            tokenizer  = tokenizer,
            train_dataset = dataset,
            args = SFTConfig(
                output_dir                  = str(adapter_path),
                per_device_train_batch_size = TRAIN_CONFIG["per_device_train_batch_size"],
                gradient_accumulation_steps = TRAIN_CONFIG["gradient_accumulation_steps"],
                num_train_epochs            = TRAIN_CONFIG["num_train_epochs"],
                learning_rate               = TRAIN_CONFIG["learning_rate"],
                warmup_steps                = TRAIN_CONFIG["warmup_steps"],
                save_steps                  = TRAIN_CONFIG["save_steps"],
                logging_steps               = TRAIN_CONFIG["logging_steps"],
                optim                       = TRAIN_CONFIG["optim"],
                lr_scheduler_type           = TRAIN_CONFIG["lr_scheduler_type"],
                bf16                        = TRAIN_CONFIG["bf16"],
                fp16                        = TRAIN_CONFIG["fp16"],
                report_to                   = "none",  # No W&B
                dataset_text_field          = "text",
                max_seq_length              = TRAIN_CONFIG["max_seq_length"],
                packing                     = True,
            ),
        )

        print(f"\n[Trainer] 🔥 Training {doctor_name}...")
        trainer.train()
        model.save_pretrained(str(adapter_path))
        tokenizer.save_pretrained(str(adapter_path))
        print(f"[Trainer] ✅ Adapter saved: {adapter_path}")

        return adapter_path

    def _export_gguf(self, adapter_path: Path, doctor_name: str, hf_model: str) -> Path:
        """
        Merge LoRA adapter + base model and export to GGUF format.
        Uses Unsloth's built-in save_pretrained_gguf.
        """
        try:
            from unsloth import FastLanguageModel
        except ImportError:
            raise ImportError("unsloth not installed")

        print(f"[Trainer] Exporting {doctor_name} to GGUF...")
        gguf_path = GGUF_DIR / f"{doctor_name.replace(' ', '_').lower()}.gguf"

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name     = str(adapter_path),
            max_seq_length = TRAIN_CONFIG["max_seq_length"],
            dtype          = None,
            load_in_4bit   = True,
        )

        model.save_pretrained_gguf(
            str(gguf_path.parent / gguf_path.stem),
            tokenizer,
            quantization_method="q4_k_m"  # Good balance of quality/size
        )

        # Unsloth appends .gguf automatically
        final_path = gguf_path.parent / f"{gguf_path.stem}-Q4_K_M.gguf"
        if not final_path.exists():
            # Try alternate naming
            candidates = list(gguf_path.parent.glob(f"{gguf_path.stem}*.gguf"))
            if candidates:
                final_path = candidates[0]
            else:
                final_path = gguf_path

        print(f"[Trainer] ✅ GGUF exported: {final_path}")
        return final_path

    def _format_alpaca(self, ex: dict, tokenizer) -> str:
        """Format training example as Alpaca instruction template."""
        instruction = ex.get("instruction", "")
        input_text  = ex.get("input", "")
        output      = ex.get("output", "")

        if input_text:
            prompt = (
                f"### Instruction:\n{instruction}\n\n"
                f"### Input:\n{input_text}\n\n"
                f"### Response:\n{output}"
            )
        else:
            prompt = (
                f"### Instruction:\n{instruction}\n\n"
                f"### Response:\n{output}"
            )
        return prompt + tokenizer.eos_token


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        # Quick check — verify imports
        try:
            import torch
            print(f"✅ PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"   GPU: {torch.cuda.get_device_name(0)}")
            from unsloth import FastLanguageModel
            print("✅ Unsloth installed")
        except ImportError as e:
            print(f"❌ Missing: {e}")
            print("   Run: pip install 'unsloth[cu121-torch250] @ git+https://github.com/unslothai/unsloth.git'")
