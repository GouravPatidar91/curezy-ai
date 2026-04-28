FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8000

# Set work directory
WORKDIR /app

# Install system dependencies (required for OpenCV and Tesseract OCR)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Pre-install CPU-only PyTorch to prevent Cloud Build Out-of-Memory crashes and reduce image size
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Cloud Run expects the container to listen on the $PORT environment variable (default 8080)
ENV PORT=8080
EXPOSE 8080

# Start command (using shell form to evaluate $PORT)
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT}"
