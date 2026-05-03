import os
import subprocess
import time
HF_TOKEN = os.getenv("HF_TOKEN")

def run_remote(command):
    full_cmd = ["gcloud", "compute", "ssh", "curezyai-std", "--zone=us-central1-a", "--command", command]
    print(f"Executing: {command}")
    process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    stdout, stderr = process.communicate()
    return process.returncode

# 1. Clear existing containers
print("Cleaning up old containers...")
run_remote("sudo docker stop aurix aura auris || true")
run_remote("sudo docker rm aurix aura auris || true")

# Safe Parallel Settings
# --enforce-eager: Disables CUDA graph capturing to save 2GB+ VRAM per instance
# --gpu-memory-utilization 0.25: Each instance gets 6GB VRAM
# --max-model-len 2048: Sufficient for clinical diagnosis context
SAFE_OPTS = "--enforce-eager --gpu-memory-utilization 0.25 --max-model-len 2048 --quantization awq"

# 2. Launch AURIX (Gemma 7B)
print("Launching AURIX (Gemma 7B AWQ)...")
run_remote(f'sudo docker run -d --name aurix --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8001:8000 --ipc=host vllm/vllm-openai:latest --model casperhansen/gemma-7b-it-awq {SAFE_OPTS}')

# 3. Launch AURA (Llama 3 8B)
print("Launching AURA (Llama 3 8B AWQ)...")
run_remote(f'sudo docker run -d --name aura --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8002:8000 --ipc=host vllm/vllm-openai:latest --model casperhansen/llama-3-8b-instruct-awq {SAFE_OPTS}')

# 4. Launch AURIS (Mistral 7B)
print("Launching AURIS (Mistral 7B AWQ)...")
run_remote(f'sudo docker run -d --name auris --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8003:8000 --ipc=host vllm/vllm-openai:latest --model TheBloke/Mistral-7B-Instruct-v0.2-AWQ {SAFE_OPTS}')

print("vLLM Eager-Parallel deployment commands sent.")
