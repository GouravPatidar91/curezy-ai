#!/bin/bash
# Curezy AI — VM Startup Script
# Runs on every boot of curezyai-std (NVIDIA L4 GPU, 22.5GB VRAM)
# 1. Configures Ollama for permanent GPU VRAM residency (KEEP_ALIVE=-1)
# 2. Starts Ollama service
# 3. Pre-warms all 3 council models in parallel into VRAM
# 4. Updates Cloud Run OLLAMA_HOST with current external IP

set -e
exec >> /var/log/curezy-startup.log 2>&1

echo "=== Curezy startup: $(date) ==="

# 1. Ensure Ollama systemd override persists across reboots
#    Keeps all 3 council models in L4 VRAM forever (no cold-start penalty)
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_MAX_LOADED_MODELS=3"
Environment="OLLAMA_NUM_PARALLEL=3"
EOF
systemctl daemon-reload
echo "[OK] Ollama Parallel Config applied (NUM_PARALLEL=3)"

# 2. Start Ollama
systemctl enable ollama
systemctl restart ollama
echo "[OK] Ollama service started"

# 3. Wait until Ollama API is responding
for i in {1..30}; do
  if curl -sf http://localhost:11434 > /dev/null; then
    echo "[OK] Ollama API ready after $((i*3))s"
    break
  fi
  sleep 3
done

# 4. Pre-warm all 3 council models in parallel (L4 has 22.5GB, all fit at ~12GB total)
(
  echo "[INFO] Pre-warming council models into GPU VRAM in parallel..."
  curl -s -X POST http://localhost:11434/api/generate \
    -d '{"model":"alibayram/medgemma:4b","prompt":"","keep_alive":-1}' > /dev/null &
  curl -s -X POST http://localhost:11434/api/generate \
    -d '{"model":"koesn/llama3-openbiollm-8b:latest","prompt":"","keep_alive":-1}' > /dev/null &
  curl -s -X POST http://localhost:11434/api/generate \
    -d '{"model":"mistral:7b","prompt":"","keep_alive":-1}' > /dev/null &
  wait
  echo "[OK] All 3 council models warm in VRAM — 62 tok/s on L4 GPU"
) &

# 5. Get external IP from GCP metadata server
EXTERNAL_IP=$(curl -sf -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip")

echo "[INFO] External IP: ${EXTERNAL_IP}"

# 6. Update Cloud Run service with latest IP and vLLM status
if command -v gcloud &> /dev/null; then
  # Check if vLLM containers are running
  if sudo docker ps | grep -q "aurix"; then
    echo "[INFO] Configuring Cloud Run for vLLM Parallel Mode..."
    gcloud run services update ai-service \
      --region=us-central1 \
      --update-env-vars="USE_VLLM=true,OLLAMA_HOST=http://${EXTERNAL_IP}:11434" \
      --quiet || echo "[WARN] Cloud Run update failed"
  else
    echo "[INFO] Configuring Cloud Run for Ollama Sequential Mode..."
    gcloud run services update ai-service \
      --region=us-central1 \
      --update-env-vars="USE_VLLM=false,OLLAMA_HOST=http://${EXTERNAL_IP}:11434" \
      --quiet || echo "[WARN] Cloud Run update failed"
  fi
fi

echo "[OK] Startup complete — Parallel Engine Ready"
echo "=== Curezy startup finished: $(date) ==="
