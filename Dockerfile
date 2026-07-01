
FROM python:3.11.4-slim 

# ==================================================
# Environment Variables
# ==================================================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=3

# ==================================================
# System Dependencies
# ==================================================
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ==================================================
# Working Directory
# ==================================================
WORKDIR /app

# ==================================================
# Install Dependencies
# ==================================================
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# ==================================================
# Copy Project Files
# ==================================================
COPY . .

# ==================================================
# Expose FastAPI Port
# ==================================================
EXPOSE 8000

# ==================================================
# Run FastAPI
# ==================================================
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]