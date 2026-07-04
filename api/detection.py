
import io
import numpy as np
import tensorflow as tf
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, MobileNetV2 #type: ignore
from tensorflow.keras import layers, models

router = APIRouter(prefix="/detect", tags=["Potato Leaf Detection"])

# ------------------------
# CONFIG
# ------------------------
MODEL_PATH = "./ml_models/detect_V1.keras"
IMG_SIZE = (224, 224)
CLASS_NAMES = ["Not_Potato", "Potato"]  # index 0, 1 -- must match training order
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


def build_architecture():
    """
    Must exactly match the architecture used during training:
    MobileNetV2 base -> GlobalAveragePooling2D -> Dense(128, relu)
    -> BatchNormalization -> Dropout -> Dense(1, sigmoid)

    If your training script's head differs, update this to match exactly --
    weights-only loading requires an identical layer-by-layer architecture.
    """
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights=None)
    inputs = layers.Input(shape=IMG_SIZE + (3,))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)
    return models.Model(inputs, outputs)


def load_model_safely(path: str):
    """
    Try the normal full-model load first (fast path).
    If it fails due to a Keras version mismatch (config deserialization
    error -- e.g. 'GlorotUniform.__init__() got an unexpected keyword
    argument input_axes'), fall back to rebuilding the architecture and
    loading only the weights, which aren't affected by config-format
    changes between Keras versions.
    """
    try:
        return tf.keras.models.load_model(path)
    except TypeError as e:
        print(f"[warn] Full model load failed ({e}); falling back to weights-only load.")
        rebuilt_model = build_architecture()
        rebuilt_model.load_weights(path)
        return rebuilt_model


# ------------------------
# LOAD MODEL ONCE AT STARTUP
# (module-level load = runs once when the app imports this router,
#  not on every request)
# ------------------------
model = load_model_safely(MODEL_PATH)


# ------------------------
# RESPONSE SCHEMA
# ------------------------
class PredictionResponse(BaseModel):
    label: str
    confidence: float
    raw_score: float


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes into a model-ready array."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file.")

    img = img.resize(IMG_SIZE)
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)  # add batch dimension
    img_array = preprocess_input(img_array)
    return img_array


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

    raw_score = float(model.predict(img_array, verbose=0)[0][0])
    predicted_index = int(raw_score > 0.5)
    label = CLASS_NAMES[predicted_index]
    confidence = raw_score if predicted_index == 1 else 1 - raw_score

    return PredictionResponse(
        label=label,
        confidence=round(confidence, 4),
        raw_score=round(raw_score, 4),
    )
    
