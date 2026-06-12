# --------------------------------------------------
# Base Image
# --------------------------------------------------
FROM python:3.11-slim

# --------------------------------------------------
# Environment
# --------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=3

# --------------------------------------------------
# System Dependencies
# --------------------------------------------------
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Work Directory
# --------------------------------------------------
WORKDIR /app

# --------------------------------------------------
# Install Python Dependencies
# --------------------------------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------
# Copy Project
# --------------------------------------------------
COPY . .

# --------------------------------------------------
# FastAPI Cloud / Render / Railway Port
# --------------------------------------------------
ENV PORT=8000

# --------------------------------------------------
# Start Server
# --------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]