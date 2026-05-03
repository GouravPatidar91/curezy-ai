import os
import subprocess

HF_TOKEN = os.getenv("HF_TOKEN")

def run_remote(command):
    full_cmd = ["gcloud", "compute", "ssh", "curezyai-std", "--zone=us-central1-a", "--command", command]
    print(f"Executing: {command}")
    process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    stdout, stderr = process.communicate()
    return process.returncode

print("Cleaning up old containers...")
run_remote("sudo docker stop aurix aura auris || true")
run_remote("sudo docker rm aurix aura auris || true")

# Common settings for stability
# AURIX (2B) uses 15% VRAM
# AURA (8B AWQ) uses 30% VRAM
# AURIS (7B AWQ) uses 25% VRAM
# Total = 70% of 24GB = 16.8GB (Safe)

print("Launching AURIX (Gemma 2B) in vLLM (Port 8001)...")
run_remote(f'sudo docker run -d --name aurix --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8001:8000 --ipc=host vllm/vllm-openai:latest --model google/gemma-1.1-2b-it --enforce-eager --gpu-memory-utilization 0.15 --max-model-len 2048')

print("Launching AURA (Llama 3 8B AWQ) in vLLM (Port 8002)...")
run_remote(f'sudo docker run -d --name aura --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8002:8000 --ipc=host vllm/vllm-openai:latest --model casperhansen/llama-3-8b-instruct-awq --enforce-eager --gpu-memory-utilization 0.30 --max-model-len 2048 --quantization awq')

print("Launching AURIS (Mistral 7B AWQ) in vLLM (Port 8003)...")
run_remote(f'sudo docker run -d --name auris --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8003:8000 --ipc=host vllm/vllm-openai:latest --model TheBloke/Mistral-7B-Instruct-v0.2-AWQ --enforce-eager --gpu-memory-utilization 0.25 --max-model-len 2048 --quantization awq')

print("All-vLLM Parallel Engine deployed.")
