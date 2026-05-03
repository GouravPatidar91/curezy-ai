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

# Launch AURA (Llama 3) in vLLM - Reserved 40% VRAM
print("Launching AURA (Llama 3 8B) in vLLM (Port 8002)...")
run_remote(f'sudo docker run -d --name aura --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8002:8000 --ipc=host vllm/vllm-openai:latest --model casperhansen/llama-3-8b-instruct-awq --enforce-eager --gpu-memory-utilization 0.40 --max-model-len 4096 --quantization awq')

# Restart Ollama for the others (AURIX and AURIS)
print("Ensuring Ollama is running for the council partners...")
run_remote("sudo systemctl restart ollama")

print("Hybrid Engine (vLLM + Ollama) deployment commands sent.")
