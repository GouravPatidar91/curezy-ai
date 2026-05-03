import os
import subprocess
import time

# Load HF_TOKEN from .env manually to avoid dependency on python-dotenv
def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k] = v
    return env_vars

env = load_env()
HF_TOKEN = env.get("HF_TOKEN") or os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("[ERROR] HF_TOKEN not found in .env or environment. vLLM needs this for gated models.")
    # In production, we'd exit here, but for this session we'll assume it's in the VM's env.

def run_remote(command):
    # This script assumes you have gcloud configured locally
    full_cmd = ["gcloud", "compute", "ssh", "curezyai-std", "--zone=us-central1-a", "--command", command]
    print(f"Executing: {command}")
    process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"[FAIL] {stderr}")
    return process.returncode

# 1. Prepare VM Environment
print("--- PREPARING VM ---")
run_remote("sudo systemctl stop ollama || true")
run_remote("sudo docker stop aurix aura auris || true")
run_remote("sudo docker rm aurix aura auris || true")

# 2. Launch Containers
# We use AWQ models for speed and VRAM efficiency on the L4.
# Total VRAM Budget (L4 = 24GB):
# AURIX (MedGemma 2B)   : 0.15 (~3.6GB)
# AURA (Llama 3 8B AWQ) : 0.35 (~8.4GB) 
# AURIS (Mistral 7B AWQ): 0.30 (~7.2GB)
# Slack / Overheads     : 0.20 (~4.8GB)

containers = [
    {
        "name": "aurix",
        "port": 8001,
        "model": "bartowski/OpenBioLLM-Llama3-8B-AWQ", 
        "util": 0.35,
        "extra": "--quantization awq"
    },
    {
        "name": "aura",
        "port": 8002,
        "model": "BioMistral/BioMistral-7B-AWQ-QGS128-W4-GEMM",
        "util": 0.30,
        "extra": "--quantization awq"
    },
    {
        "name": "auris",
        "port": 8003,
        "model": "casperhansen/llama-3-8b-instruct-awq",
        "util": 0.25,
        "extra": "--quantization awq"
    }
]

print("--- LAUNCHING MEDICAL AWQ COUNCIL (vLLM) ---")
for c in containers:
    cmd = (
        f"sudo docker run -d --name {c['name']} "
        f"--runtime nvidia --gpus '\"device=0\"' "
        f"-v ~/.cache/huggingface:/root/.cache/huggingface "
        f"-p {c['port']}:8000 "
        f"--ipc=host "
        f"-e HUGGING_FACE_HUB_TOKEN={HF_TOKEN} "
        f"vllm/vllm-openai:v0.6.3.post1 "
        f"--model {c['model']} "
        f"--gpu-memory-utilization {c['util']} "
        f"--max-model-len 4096 "
        f"{c['extra']}"
    )
    run_remote(cmd)
    time.sleep(15) # Wait for each to claim VRAM

print("\n--- STATUS ---")
run_remote("sudo docker ps")
print("\n[INFO] Models are downloading/booting. This will take 5-10 minutes.")
print("[INFO] Check logs with: gcloud compute ssh curezyai-std --command 'sudo docker logs -f aura'")
