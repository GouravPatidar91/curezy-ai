import os
import subprocess

HF_TOKEN = os.getenv("HF_TOKEN")

def run_remote(command):
    full_cmd = ["gcloud", "compute", "ssh", "curezyai-std", "--zone=us-central1-a", "--command", command]
    print(f"Executing: {command}")
    process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    stdout, stderr = process.communicate()
    if stdout: print(f"STDOUT: {stdout}")
    if stderr: print(f"STDERR: {stderr}")
    return process.returncode

# FIXING AURIS (Mistral)
print("Updating AURIS to a more reliable AWQ quant...")
run_remote("sudo docker stop auris || true")
run_remote("sudo docker rm auris || true")
# Using TheBloke v0.2 which is very reliable and often doesn't need gating tokens
run_remote(f'sudo docker run -d --name auris --runtime nvidia --gpus "\\"device=0\\"" -e HF_TOKEN={HF_TOKEN} -v ~/.cache/huggingface:/root/.cache/huggingface -p 8003:8000 --ipc=host vllm/vllm-openai:latest --model TheBloke/Mistral-7B-Instruct-v0.2-AWQ --quantization awq --gpu-memory-utilization 0.25 --max-model-len 4096')

print("AURIS update sent.")
