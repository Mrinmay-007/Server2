    
import io
import os
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from PIL import Image


try:
    from ai_edge_litert.interpreter import Interpreter  # type: ignore
except ImportError:
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore
    except ImportError:
        import tensorflow as tf
        Interpreter = tf.lite.Interpreter

router = APIRouter(prefix="/detect", tags=["Potato Leaf Detection"])

# ------------------------
# CONFIG
# BASE_DIR goes up two levels: api/detection_tf_lite.py -> api/ -> project root
# ------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "detect_V1.tflite")

CLASS_NAMES = ["Not_Potato", "Potato"]  # index 0, 1 -- must match training order
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
IMG_SIZE = (224, 224)

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if os.path.getsize(MODEL_PATH) == 0:
    raise ValueError(f"Model file is empty: {MODEL_PATH}")

# ------------------------
# LOAD MODEL
# ------------------------
interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

_input_details = interpreter.get_input_details()
_output_details = interpreter.get_output_details()
_input_index = _input_details[0]["index"]
_output_index = _output_details[0]["index"]


# ------------------------
# RESPONSE SCHEMA
# ------------------------
class PredictionResponse(BaseModel):
    label: str
    confidence: float
    raw_score: float


def mobilenet_v2_preprocess(img_array: np.ndarray) -> np.ndarray:
    """
    Replicates tf.keras.applications.mobilenet_v2.preprocess_input
    without needing the full tensorflow package: scales pixels from
    [0, 255] to [-1, 1].
    """
    img_array = img_array.astype(np.float32)
    img_array = (img_array / 127.5) - 1.0
    return img_array


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes into a TFLite-ready array."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file.")

    img = img.resize(IMG_SIZE)
    img_array = np.array(img, dtype=np.float32)
    img_array = mobilenet_v2_preprocess(img_array)
    img_array = np.expand_dims(img_array, axis=0)  # add batch dimension
    return img_array


def run_inference(img_array: np.ndarray) -> float:
    """Run a single forward pass through the TFLite interpreter."""
    interpreter.set_tensor(_input_index, img_array)
    interpreter.invoke()
    output = interpreter.get_tensor(_output_index)
    return float(output[0][0])


# -------------------------------
# Health Check
# -------------------------------
@router.get("/ping")
async def ping():
    return {"message": "Detection API is running"}


@router.post("/", response_model=PredictionResponse)
async def predict_potato_leaf(file: UploadFile = File(...)):
    """
    Upload a leaf image and get a prediction: Potato or Not_Potato.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Please upload a JPEG, PNG, or WEBP image.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    img_array = preprocess_image(image_bytes)
    raw_score = run_inference(img_array)

    predicted_index = int(raw_score > 0.5)
    label = CLASS_NAMES[predicted_index]
    confidence = raw_score if predicted_index == 1 else 1 - raw_score

    return PredictionResponse(
        label=label,
        confidence=round(confidence, 4),
        raw_score=round(raw_score, 4),
    )