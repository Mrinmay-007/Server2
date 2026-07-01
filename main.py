

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ============================
# Download models first
# ============================
from utils.download_models import download_models

download_models()

# ============================
# Import routers AFTER models exist
# ============================
from api import prediction, detection

# ============================
# FastAPI app
# ============================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Include Routers
# ============================
app.include_router(prediction.router)
app.include_router(detection.router)

# ============================
# Run App
# ============================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True
    )