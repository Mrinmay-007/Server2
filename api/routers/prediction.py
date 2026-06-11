
from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf
import os
import cv2
from functools import lru_cache

# -------------------------------
# TensorFlow Optimization
# -------------------------------
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

router = APIRouter(
    prefix="/predict",
    tags=["Disease Prediction"]
)

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "V1.keras")

CLASS_NAMES = [
    "Early Blight",
    "Late Blight",
    "Healthy"
]

# -------------------------------
# Lazy Load Model
# -------------------------------
@lru_cache(maxsize=1)
def get_model():
    print("Loading disease model...")
    model = tf.keras.models.load_model(
        MODEL_PATH,
        compile=False
    )
    print("Disease model loaded.")
    return model

# -------------------------------
# Health Check
# -------------------------------
@router.get("/ping")
async def ping():
    return {"status": "ok"}

# -------------------------------
# Image Processing
# -------------------------------
def read_file_as_image(data: bytes):

    image = Image.open(BytesIO(data))

    if image.mode != "RGB":
        image = image.convert("RGB")

    image = image.resize((256, 256))

    image = np.asarray(image, dtype=np.float32)

    image /= 255.0

    return np.expand_dims(image, axis=0)

# -------------------------------
# Severity Detection
# -------------------------------
def get_severity_from_bytes(image_bytes: bytes):

    np_arr = np.frombuffer(image_bytes, np.uint8)

    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return "Unknown", 0.0

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    leaf_mask = cv2.inRange(
        hsv,
        np.array([25, 40, 40]),
        np.array([85, 255, 255])
    )

    disease_mask = cv2.inRange(
        hsv,
        np.array([0, 0, 0]),
        np.array([180, 255, 80])
    )

    infected_mask = cv2.bitwise_and(
        disease_mask,
        leaf_mask
    )

    infected_area = np.count_nonzero(infected_mask)
    total_leaf_area = np.count_nonzero(leaf_mask)

    ratio = (
        infected_area / total_leaf_area * 100
        if total_leaf_area > 0
        else 0
    )

    if ratio < 10:
        severity = "Mild"
    elif ratio < 30:
        severity = "Moderate"
    else:
        severity = "Severe"

    return severity, ratio

# -------------------------------
# Prediction Endpoint
# -------------------------------
@router.post("/")
async def predict(file: UploadFile = File(...)):

    try:
        file_bytes = await file.read()

        image = read_file_as_image(file_bytes)

        model = get_model()

        predictions = model(
            image,
            training=False
        ).numpy()

        predicted_class = CLASS_NAMES[
            np.argmax(predictions[0])
        ]

        confidence = float(
            np.max(predictions[0])
        )

        severity = "N/A"
        ratio = 0.0

        if predicted_class != "Healthy":
            severity, ratio = get_severity_from_bytes(
                file_bytes
            )

        return {
            "class": predicted_class,
            "confidence": round(confidence * 100, 2),
            "severity": severity,
            "infected_ratio": round(ratio, 2)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )