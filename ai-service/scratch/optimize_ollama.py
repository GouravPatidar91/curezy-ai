import subprocess

def run_remote(command):
    full_cmd = ["gcloud", "compute", "ssh", "curezyai-std", "--zone=us-central1-a", "--command", command]
    print(f"Executing: {command}")
    process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    stdout, stderr = process.communicate()
    return process.returncode

print("Stopping all vLLM containers to reclaim VRAM...")
run_remote("sudo docker stop aurix aura auris || true")
run_remote("sudo docker rm aurix aura auris || true")

print("Applying High-Performance Parallel Ollama Config...")
# Set OLLAMA_NUM_PARALLEL=4 (Concurrent inference)
# Set OLLAMA_MAX_LOADED_MODELS=4 (Keep all council models in VRAM)
# Set OLLAMA_FLASH_ATTENTION=1 (Speed up inference)
run_remote('sudo mkdir -p /etc/systemd/system/ollama.service.d')
config_content = '[Service]\\nEnvironment="OLLAMA_NUM_PARALLEL=4"\\nEnvironment="OLLAMA_MAX_LOADED_MODELS=4"\\nEnvironment="OLLAMA_FLASH_ATTENTION=1"'
run_remote(f'echo -e "{config_content}" | sudo tee /etc/systemd/system/ollama.service.d/parallel.conf')

print("Restarting Ollama with new performance settings...")
run_remote("sudo systemctl daemon-reload")
run_remote("sudo systemctl restart ollama")

print("Ollama optimization complete.")
