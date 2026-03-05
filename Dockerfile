# ─────────────────────────────────────────────────────────────
# Curezy AURANET — RunPod Serverless Dockerfile
# Base: RunPod PyTorch + CUDA 12.4
#
# NOTE: Models are NOT baked into this image (keeps build fast).
# They are downloaded on first container startup via runpod_handler.py.
# On RunPod Serverless, use a Network Volume to cache models between runs.
# ─────────────────────────────────────────────────────────────
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /app

# ── System deps ────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    curl wget git zstd tesseract-ocr libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ── Install Ollama (install.sh works reliably on Linux) ───────
RUN curl -fsSL https://ollama.com/install.sh | sh

# ── Python dependencies ────────────────────────────────────────
COPY ai-service/requirements.txt .
RUN pip install --no-cache-dir runpod ollama \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir spacy scispacy \
    && pip install --no-cache-dir https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_scibert-0.5.4.tar.gz

# ── Copy codebase ──────────────────────────────────────────────
COPY ai-service/ .

# ── Entry point ────────────────────────────────────────────────
CMD ["python", "-u", "runpod_handler.py"]

