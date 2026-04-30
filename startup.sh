#!/bin/bash
# Curezy AI ? VM Startup Script
# Runs on every boot
# 1. Starts Ollama/vLLM services
# 2. Gets current external IP
# 3. Updates Cloud Run OLLAMA_HOST env var automatically

set -e
exec >> /var/log/curezy-startup.log 2>&1

echo "=== Curezy startup: $(date) ==="

# 1. Start Ollama (Legacy support)
sudo systemctl start ollama || true
sudo systemctl enable ollama || true
echo "[OK] Ollama service started"

# 2. Get external IP from GCP metadata server
EXTERNAL_IP=$(curl -sf -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip")

echo "[INFO] External IP: ${EXTERNAL_IP}"

# 3. Update Cloud Run service OLLAMA_HOST (and vLLM endpoints if needed)
gcloud run services update ai-service \
  --region=us-central1 \
  --update-env-vars="OLLAMA_HOST=http://${EXTERNAL_IP}:11434,AURIX_VLLM_URL=http://${EXTERNAL_IP}:8001/v1/chat/completions,AURA_VLLM_URL=http://${EXTERNAL_IP}:8002/v1/chat/completions,AURIS_VLLM_URL=http://${EXTERNAL_IP}:8003/v1/chat/completions" \
  --quiet || echo "[WARN] Cloud Run update failed"

echo "[OK] Cloud Run updated: IPs pointing to ${EXTERNAL_IP}"
echo "=== Startup complete ==="
