
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# from utils.download_models import download_models

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# logger.info("Ensuring models are downloaded...")
# download_models()
# logger.info("Models ready.")

from api import prediction_tf_lite
from api import detection_tf_lite

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_tf_lite.router)
app.include_router(detection_tf_lite.router)


@app.get("/")
def root():
    return {"message": "API Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)