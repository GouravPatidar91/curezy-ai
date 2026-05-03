#!/bin/bash
set -e

echo "Starting vLLM Infrastructure Setup for Curezy AI..."

# 0. Stop Ollama to free up VRAM
echo "[INFO] Stopping Ollama..."
sudo systemctl stop ollama || true

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[INFO] Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# 2. Install NVIDIA Container Toolkit if not present
if ! command -v nvidia-ctk &> /dev/null; then
    echo "[INFO] Installing NVIDIA Container Toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
fi

echo "[INFO] Starting vLLM Containers (Parallel Inference)..."

# Stop and remove existing if any
sudo docker stop aurix aura auris || true
sudo docker rm aurix aura auris || true

# 3. Launch AURIX (MedGemma 4B) - Port 8001
sudo docker run -d --name aurix \
  --runtime nvidia --gpus '"device=0"' \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8001:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model alibayram/medgemma-4b \
  --gpu-memory-utilization 0.30 \
  --max-model-len 4096

# 4. Launch AURA (OpenBioLLM 8B AWQ) - Port 8002
sudo docker run -d --name aura \
  --runtime nvidia --gpus '"device=0"' \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8002:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model casperhansen/llama-3-openbiollm-8b-awq \
  --quantization awq \
  --gpu-memory-utilization 0.30 \
  --max-model-len 4096

# 5. Launch AURIS (Mistral 7B AWQ) - Port 8003
sudo docker run -d --name auris \
  --runtime nvidia --gpus '"device=0"' \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8003:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model MaziyarPanahi/Mistral-7B-Instruct-v0.3-AWQ \
  --quantization awq \
  --gpu-memory-utilization 0.25 \
  --max-model-len 4096

echo "vLLM Containers are booting up!"
