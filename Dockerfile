
FROM python:3.11-slim

# ==================================================
# Environment Variables
# ==================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=3

# ==================================================
# System Dependencies
# opencv-python-headless needs these runtime libs even without a display.
# gcc/g++/ffmpeg were only needed for building full tensorflow from source
# in some environments -- removed now that we use the lightweight
# ai-edge-litert package (prebuilt wheels, nothing to compile).
# ==================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Working Directory
# ==================================================
WORKDIR /app

# ==================================================
# Install Python Dependencies
# ==================================================
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==================================================
# Copy Application
# ==================================================
COPY . .

# ==================================================
# Expose Port
# ==================================================
EXPOSE 8000

# ==================================================
# Start Application
# Uses ${PORT:-8000} so this also works on platforms (Render, Railway,
# Cloud Run, etc.) that inject a dynamic PORT env var, while still
# defaulting to 8000 for plain `docker run` / local testing.
# Shell form is required here for the ${PORT:-8000} expansion to work.
# ==================================================
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

