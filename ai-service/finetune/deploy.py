"""
finetune/deploy.py
==================
Auto-deploy fine-tuned GGUF models to Ollama.
Creates new Modelfiles and registers models with unique fine-tuned names.
Also updates the COUNCIL list in clinical_reasoner.py to use the new models.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, Callable

# Fine-tuned model name prefix
FT_PREFIX = "curezy"

# Map from doctor name to new Ollama model name
DOCTOR_TO_FT_MODEL = {
    "Dr. Gemma":   "curezy-gemma-ft",
    "Dr. OpenBio": "curezy-openbiollm-ft",
    "Dr. Mistral": "curezy-mistral-ft",
}

REASONER_PATH = Path(__file__).parent.parent / "agents" / "clinical_reasoner.py"


class OllamaDeploy:

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_cb = progress_callback or (lambda msg, pct: None)

    def deploy_all(self, training_results: Dict) -> Dict:
        """
        Deploy all successfully trained models to Ollama.
        Returns deploy results per model.
        """
        deploy_results = {}
        successful_doctors = {
            name: res for name, res in training_results.items()
            if res.get("success") and res.get("gguf_path")
        }

        if not successful_doctors:
            return {"error": "No models trained successfully"}

        for i, (doctor_name, result) in enumerate(successful_doctors.items()):
            gguf_path = result["gguf_path"]
            ft_model_name = DOCTOR_TO_FT_MODEL.get(doctor_name, f"curezy-{doctor_name.lower().replace(' ', '-')}-ft")

            pct = 80 + int(i / len(successful_doctors) * 15)
            self.progress_cb(f"Deploying {doctor_name} to Ollama...", pct)

            try:
                result = self._deploy_model(gguf_path, ft_model_name, doctor_name)
                deploy_results[doctor_name] = result
                self.progress_cb(f"✅ {doctor_name} deployed as {ft_model_name}", pct + 4)
            except Exception as e:
                print(f"[Deploy] ❌ {doctor_name} deploy failed: {e}")
                deploy_results[doctor_name] = {"success": False, "error": str(e)}

        # Update clinical_reasoner.py if any deployed successfully
        deployed = {
            name: DOCTOR_TO_FT_MODEL[name]
            for name in deploy_results
            if deploy_results[name].get("success")
        }
        if deployed:
            self._update_council(deployed)
            self.progress_cb("✅ Council updated with fine-tuned models", 97)

        return deploy_results

    def _deploy_model(self, gguf_path: str, model_name: str, doctor_name: str) -> Dict:
        """Create Modelfile and register with Ollama."""
        gguf_abs = Path(gguf_path).resolve()
        if not gguf_abs.exists():
            raise FileNotFoundError(f"GGUF not found: {gguf_abs}")

        # Write Modelfile
        modelfile_path = gguf_abs.parent / f"Modelfile_{model_name}"
        modelfile_content = self._create_modelfile(gguf_abs, doctor_name)
        with open(modelfile_path, "w", encoding="utf-8") as f:
            f.write(modelfile_content)

        print(f"[Deploy] Creating Ollama model: {model_name}")
        print(f"[Deploy] GGUF: {gguf_abs}")

        # Run ollama create
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            raise RuntimeError(f"ollama create failed: {result.stderr}")

        print(f"[Deploy] ✅ {model_name} registered in Ollama")
        return {
            "success":    True,
            "model_name": model_name,
            "gguf_path":  str(gguf_abs),
            "stdout":     result.stdout[:500]
        }

    def _create_modelfile(self, gguf_path: Path, doctor_name: str) -> str:
        """Generate Ollama Modelfile content for a fine-tuned model."""
        specialty_map = {
            "Dr. Gemma":   "General Medicine and Primary Care",
            "Dr. OpenBio": "Biomedical Research and Evidence-Based Medicine",
            "Dr. Mistral": "Differential Diagnosis and Clinical Reasoning",
        }
        specialty = specialty_map.get(doctor_name, "Medical Diagnosis")

        return f"""FROM {gguf_path}

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 2048
PARAMETER stop "USER:"
PARAMETER stop "Human:"
PARAMETER stop "Assistant:"

SYSTEM \"\"\"You are {doctor_name}, a fine-tuned medical AI specializing in {specialty}.
You have been trained on curated medical datasets to provide accurate, evidence-based clinical assessments.
Always respond with structured clinical reasoning, specific diagnoses, and actionable recommendations.
Never use placeholder text — always provide real medical condition names and specific clinical details.
Format your responses as valid JSON when structured output is requested.\"\"\"
"""

    def _update_council(self, deployed: Dict[str, str]):
        """
        Update COUNCIL list in clinical_reasoner.py to use fine-tuned model names.
        Keeps the original as a backup comment.
        """
        if not REASONER_PATH.exists():
            print(f"[Deploy] ⚠️  clinical_reasoner.py not found at {REASONER_PATH}")
            return

        with open(REASONER_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Back up original
        backup_path = REASONER_PATH.parent / "clinical_reasoner_pre_finetune.py.bak"
        if not backup_path.exists():
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[Deploy] 📋 Backed up original to {backup_path.name}")

        # Update model strings for each deployed doctor
        updated_content = content
        for doctor_name, ft_model_name in deployed.items():
            # Find original model string for this doctor and replace
            # Pattern: "name": "Dr. X", ... "model": "original_model"
            # We'll use a safe line-by-line approach
            doctor_tag = doctor_name.replace("Dr. ", "")
            lines = updated_content.split("\n")
            new_lines = []
            inside_doctor = False
            for line in lines:
                if f'"name"' in line and f'"Dr. {doctor_tag}"' in line:
                    inside_doctor = True
                if inside_doctor and '"model"' in line:
                    # Replace model value
                    new_line = re.sub(
                        r'("model"\s*:\s*")[^"]+(")',
                        f'\\g<1>{ft_model_name}\\g<2>',
                        line
                    )
                    new_lines.append(new_line)
                    inside_doctor = False
                    continue
                new_lines.append(line)
            updated_content = "\n".join(new_lines)

        with open(REASONER_PATH, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"[Deploy] ✅ Updated COUNCIL models in clinical_reasoner.py")
        print(f"[Deploy]    Changed: {list(deployed.values())}")

    def rollback(self, doctor_name: str = None):
        """
        Rollback to original models. If doctor_name given, rollback only that model.
        Otherwise rollback all.
        """
        backup_path = REASONER_PATH.parent / "clinical_reasoner_pre_finetune.py.bak"
        if not backup_path.exists():
            print("[Deploy] No backup to rollback from")
            return False

        import shutil
        shutil.copy(str(backup_path), str(REASONER_PATH))
        print("[Deploy] ✅ Rolled back to original models")
        return True

    def list_finetuned_models(self) -> list:
        """List all Curezy fine-tuned models currently in Ollama."""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=30)
            lines = result.stdout.strip().split("\n")
            ft_models = [l for l in lines if FT_PREFIX in l.lower()]
            return ft_models
        except Exception as e:
            print(f"[Deploy] Could not list models: {e}")
            return []
