"""
ollama_rename.py
================
Renames Curezy Council models inside Ollama to match the new brand names:

  alibayram/medgemma:4b             →  curezy-aurix
  koesn/llama3-openbiollm-8b:latest →  curezy-aura
  mistral:7b                        →  curezy-auris

Usage:
  python ollama_rename.py            # rename all three
  python ollama_rename.py --check    # just check which models exist
  python ollama_rename.py --delete   # rename + delete old names

How it works:
  Ollama has no rename command, so we create a new Modelfile that points
  to the existing model (FROM <original>) and register it under the new name.
"""

import subprocess
import sys
import tempfile
import os

# ── Mapping: (original_ollama_name, new_brand_name, system_prompt) ────────────
RENAMES = [
    (
        "alibayram/medgemma:4b",
        "curezy-aurix",
        "You are Curezy AURIX, the most powerful AI in the Curezy Council. "
        "You specialize in General Medicine and Primary Care. "
        "Provide thorough, evidence-based clinical assessments with structured reasoning."
    ),
    (
        "koesn/llama3-openbiollm-8b:latest",
        "curezy-aura",
        "You are Curezy AURA, the balanced AI in the Curezy Council. "
        "You specialize in Biomedical Research and Evidence-Based Medicine. "
        "Validate clinical evidence and cite research when possible."
    ),
    (
        "mistral:7b",
        "curezy-auris",
        "You are Curezy AURIS, the fast and agile AI in the Curezy Council. "
        "You specialize in Differential Diagnosis. "
        "Challenge assumptions, identify alternative diagnoses, and flag missed findings."
    ),
]


def run(cmd: list[str], check=True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ❌ Error: {result.stderr.strip()}")
    elif result.stdout.strip():
        print(f"  {result.stdout.strip()[:200]}")
    return result


def list_models() -> set[str]:
    result = run(["ollama", "list"], check=False)
    lines = result.stdout.strip().split("\n")[1:]  # skip header
    names = set()
    for line in lines:
        parts = line.split()
        if parts:
            names.add(parts[0])
    return names


def model_exists(name: str, available: set[str]) -> bool:
    # Match with or without :latest tag
    return name in available or name.split(":")[0] in available or any(
        a.startswith(name.split(":")[0]) for a in available
    )


def create_branded_model(source: str, brand_name: str, system_prompt: str, available: set) -> bool:
    """Create a new Ollama model with Curezy brand name pointing to the source model."""
    if not model_exists(source, available):
        print(f"  ⚠️  Source model '{source}' not found in Ollama — skipping.")
        print(f"      Pull it first:  ollama pull {source}")
        return False

    modelfile_content = f"""FROM {source}

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 2048
PARAMETER stop "USER:"
PARAMETER stop "Human:"
PARAMETER stop "Assistant:"

SYSTEM \"\"\"{system_prompt}\"\"\"
"""
    # Write temp Modelfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".Modelfile", delete=False, encoding="utf-8") as f:
        f.write(modelfile_content)
        tmp_path = f.name

    print(f"\n  Creating '{brand_name}' from '{source}'...")
    result = run(["ollama", "create", brand_name, "-f", tmp_path])
    os.unlink(tmp_path)

    if result.returncode == 0:
        print(f"  ✅ '{brand_name}' registered in Ollama!")
        return True
    return False


def delete_old_model(original: str, available: set) -> bool:
    """Remove the original model name from Ollama (optional cleanup)."""
    if not model_exists(original, available):
        return False
    print(f"  Removing old model name '{original}'...")
    result = run(["ollama", "rm", original], check=False)
    return result.returncode == 0


def main():
    check_only = "--check" in sys.argv
    delete_old = "--delete" in sys.argv

    print("\n" + "="*60)
    print("  Curezy — Ollama Model Renaming Tool")
    print("="*60)

    print("\n📋 Current Ollama models:")
    available = list_models()
    for m in sorted(available):
        print(f"  • {m}")

    if check_only:
        print("\n📊 Rename preview (--check mode, no changes made):")
        for source, brand_name, _ in RENAMES:
            exists = model_exists(source, available)
            already_branded = model_exists(brand_name, available)
            status = "✅ source found" if exists else "⚠️  source MISSING"
            branded = " | already branded ✅" if already_branded else ""
            print(f"  {source:45} → {brand_name}   [{status}{branded}]")
        return

    print("\n🔄 Renaming models to Curezy brand names...")
    success_count = 0
    for source, brand_name, system_prompt in RENAMES:
        already_branded = model_exists(brand_name, available)
        if already_branded:
            print(f"\n  ⏭️  '{brand_name}' already exists — skipping.")
            success_count += 1
            continue

        ok = create_branded_model(source, brand_name, system_prompt, available)
        if ok:
            success_count += 1
            if delete_old:
                delete_old_model(source, available)

    print("\n" + "="*60)
    print(f"  Done: {success_count}/{len(RENAMES)} models branded successfully.")
    print("\n  Your Curezy AURANET council now uses:")
    print("    curezy-aurix  — most powerful  (General Medicine)")
    print("    curezy-aura   — balanced        (Biomedical Research)")
    print("    curezy-auris  — fast/agile      (Differential Diagnosis)")
    print("="*60 + "\n")

    if success_count == len(RENAMES):
        print("⚡ Next step: update COUNCIL 'model' fields in clinical_reasoner.py")
        print("   to use 'curezy-aurix', 'curezy-aura', 'curezy-auris' if you want")
        print("   Ollama to serve under the branded names.\n")


if __name__ == "__main__":
    main()
