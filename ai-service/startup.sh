#!/bin/bash
# Curezy AI — VM Startup Script
# Runs on every boot (including after Spot VM restarts)
# 1. Starts Ollama service
# 2. Gets current external IP
# 3. Updates Cloud Run OLLAMA_HOST env var automatically

set -e
exec >> /var/log/curezy-startup.log 2>&1

echo "=== Curezy startup: $(date) ==="

# 1. Start Ollama
sudo systemctl start ollama
sudo systemctl enable ollama
echo "[OK] Ollama service started"

# 2. Wait until Ollama API is responding
for i in {1..20}; do
  if curl -sf http://localhost:11434 > /dev/null; then
    echo "[OK] Ollama API ready after ${i}s"
    break
  fi
  sleep 3
done

# Pre-warm models into VRAM (in background)
(
  echo "[INFO] Pre-warming models..."
  curl -s -X POST http://localhost:11434/api/generate -d '{"model": "alibayram/medgemma:4b", "keep_alive": -1}' > /dev/null
  curl -s -X POST http://localhost:11434/api/generate -d '{"model": "koesn/llama3-openbiollm-8b:latest", "keep_alive": -1}' > /dev/null
  curl -s -X POST http://localhost:11434/api/generate -d '{"model": "mistral:7b", "keep_alive": -1}' > /dev/null
  echo "[OK] Models pre-warmed"
) &

# 3. Get external IP from GCP metadata server
EXTERNAL_IP=$(curl -sf -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip")

echo "[INFO] External IP: ${EXTERNAL_IP}"

# 4. Update Cloud Run service OLLAMA_HOST
gcloud run services update ai-service \
  --region=us-central1 \
  --update-env-vars="OLLAMA_HOST=http://${EXTERNAL_IP}:11434" \
  --quiet

echo "[OK] Cloud Run updated: OLLAMA_HOST=http://${EXTERNAL_IP}:11434"
echo "=== Startup complete ==="
