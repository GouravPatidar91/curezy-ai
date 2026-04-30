"""
quantize_models.py — Curezy AURANET Model Quantization
=======================================================
NOTE: This script runs on the GCP VM (curezyai-std), NOT locally.
      awq and transformers are installed in the GCP VM venv only.

Usage (run inside SSH on curezyai-std):
  python scripts/quantize_models.py --model google/medgemma-4b-it --output ./models/medgemma-awq
  python scripts/quantize_models.py --model aaditya/Llama3-OpenBioLLM-8B --output ./models/openbiollm-awq
  python scripts/quantize_models.py --model mistralai/Mistral-7B-Instruct-v0.3 --output ./models/mistral-awq
"""

import os
import tempfile
import argparse

# ── Fix /tmp before heavy imports (handles fresh VMs where /tmp may be broken)
for _tmp_candidate in ["/tmp", "/var/tmp", os.path.expanduser("~/tmp")]:
    try:
        os.makedirs(_tmp_candidate, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=_tmp_candidate, delete=True):
            pass
        os.environ["TMPDIR"] = _tmp_candidate
        tempfile.tempdir = _tmp_candidate
        break
    except Exception:
        continue

# ── GPU/ML imports — only available on GCP VM venv, not local Windows ─────────
try:
    from awq import AutoAWQForCausalLM  # type: ignore[import]
    from transformers import AutoTokenizer  # type: ignore[import]
except ImportError as _e:
    raise SystemExit(
        f"\n[ERROR] Missing dependency: {_e}\n"
        "This script must run on the GCP VM (curezyai-std) inside the venv.\n"
        "Run: ssh curezyai-std → cd ~/curezy-ai/ai-service → source venv/bin/activate\n"
        "Then install: pip install autoawq transformers\n"
    ) from _e


def quantize_model(model_path: str, quant_path: str) -> None:
    """Quantize a HuggingFace model to 4-bit AWQ and save it locally."""
    print(f"Quantizing {model_path} -> {quant_path}...")

    try:
        model = AutoAWQForCausalLM.from_pretrained(
            model_path,
            low_cpu_mem_usage=True,
            use_cache=False,
            safetensors=True,
        )
    except OSError:
        print(f"No safetensors for {model_path} — falling back to .bin weights...")
        model = AutoAWQForCausalLM.from_pretrained(
            model_path,
            low_cpu_mem_usage=True,
            use_cache=False,
            safetensors=False,
        )

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    quant_config = {
        "zero_point": True,
        "q_group_size": 128,
        "w_bit": 4,
        "version": "GEMM",
    }

    model.quantize(tokenizer, quant_config=quant_config)
    model.save_quantized(quant_path)
    tokenizer.save_pretrained(quant_path)
    print(f"✅ Quantization complete: {quant_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Curezy AURANET — AWQ 4-bit model quantization"
    )
    parser.add_argument("--model", type=str, required=True, help="HF model ID or local path")
    parser.add_argument("--output", type=str, required=True, help="Output directory for AWQ model")
    args = parser.parse_args()

    quantize_model(args.model, args.output)
