# ==============================================================================
# Dockerfile Multi-Stage pour AlternIA Backend (FastAPI + AI Engine + Kiosk)
# ==============================================================================

FROM python:3.11-slim as base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Installation des dépendances système requises (Compilation, Audio, OCR, PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libportaudio2 \
    libasound2 \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des packages Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Copie de l'intégralité du code source
COPY . .

# Exposition du port 8000
EXPOSE 8000

# Commande de démarrage par défaut : 4 workers pour t3.xlarge
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips=*"]
