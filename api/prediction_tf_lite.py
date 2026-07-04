    
from fastapi import File, UploadFile, APIRouter, HTTPException
import numpy as np
from io import BytesIO
from PIL import Image
import os
import logging
import cv2
import threading

# ------------------------
# TFLite runtime import (same preference order as detection_tf_lite.py,
# kept consistent across both routers so the app only needs one heavy
# dependency path, not two different ones).
# ------------------------
try:
    from ai_edge_litert.interpreter import Interpreter  # type: ignore
except ImportError:
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore
    except ImportError:
        import tensorflow as tf
        Interpreter = tf.lite.Interpreter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"],
)

# -------------------------------
# Define Model Path
# -------------------------------
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "V1.tflite"
)

# -------------------------------
# Validate Model Path
# -------------------------------
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

if os.path.getsize(MODEL_PATH) == 0:
    raise ValueError(f"Model file is empty: {MODEL_PATH}")

# -------------------------------
# Load TFLite Model
# -------------------------------
logger.info("Loading disease model (TFLite)...")

INTERPRETER = Interpreter(model_path=MODEL_PATH)
INTERPRETER.allocate_tensors()

_raw_input_details = INTERPRETER.get_input_details()

# The source Keras model was built with a fixed batch_shape of 32
# (InputLayer batch_shape=[32, 256, 256, 3]), so the converted TFLite
# graph expects a batch of exactly 32 images. Since we predict on one
# image at a time, we try to resize the input tensor to batch size 1.
#
# IMPORTANT: if resize_tensor_input() succeeds but the following
# allocate_tensors() then fails (because some downstream op, e.g. the
# Flatten/Dense layers, has a shape baked in for batch=32), the
# interpreter is left in a broken, partially-resized state where tensors
# report as "unallocated" for every subsequent request. In that case we
# must discard it and build a brand new interpreter at the model's
# original fixed batch size, then pad each request up to that batch
# instead of trying to resize.
_input_index = _raw_input_details[0]["index"]
_target_shape = [1] + list(_raw_input_details[0]["shape"][1:])

try:
    INTERPRETER.resize_tensor_input(_input_index, _target_shape)
    INTERPRETER.allocate_tensors()
    logger.info("Resized TFLite input tensor to batch size 1: %s", _target_shape)
except Exception as resize_error:
    logger.warning(
        "Could not resize input tensor to batch 1 (%s). "
        "Rebuilding interpreter at the model's original fixed batch size "
        "and padding each request instead.",
        resize_error,
    )
    # The interpreter above may now be in a broken state -- don't reuse it.
    INTERPRETER = Interpreter(model_path=MODEL_PATH)
    INTERPRETER.allocate_tensors()

INPUT_DETAILS = INTERPRETER.get_input_details()
OUTPUT_DETAILS = INTERPRETER.get_output_details()
FIXED_BATCH_SIZE = INPUT_DETAILS[0]["shape"][0]  # 1 if resize succeeded, else 32

# TFLite interpreters are NOT thread-safe. FastAPI can process requests
# concurrently, so without this lock, two overlapping requests can corrupt
# each other's tensors mid-inference -- one of the most common causes of
# "same/garbage output for every input" with a shared interpreter instance.
INTERPRETER_LOCK = threading.Lock()

logger.info(
    "Disease model loaded successfully. Input shape: %s, dtype: %s",
    INPUT_DETAILS[0]["shape"],
    INPUT_DETAILS[0]["dtype"],
)

CLASS_NAMES = [
    "Early Blight",
    "Late Blight",
    "Healthy"
]

IMAGE_SIZE = 256


# -------------------------------
# Read Image
# -------------------------------
def read_file_as_image(data: bytes) -> np.ndarray:
    image = Image.open(BytesIO(data)).convert("RGB")
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
    image = np.array(image)
    return image


# -------------------------------
# TFLite Inference
# -------------------------------
def run_tflite_inference(img_batch: np.ndarray) -> np.ndarray:
    """
    Runs a single forward pass through the TFLite interpreter.

    Casts the input to whatever dtype the model actually expects
    (float32 for a standard model, uint8/int8 if it were quantized)
    instead of assuming float32 -- a mismatched dtype is a common
    cause of flat/identical predictions across different inputs.
    """
    input_detail = INPUT_DETAILS[0]
    expected_dtype = input_detail["dtype"]

    # If the model is quantized, apply its quantization params.
    scale, zero_point = input_detail.get("quantization", (0.0, 0))
    if expected_dtype in (np.uint8, np.int8) and scale not in (0.0, None):
        img_batch = (img_batch / scale + zero_point).astype(expected_dtype)
    else:
        img_batch = img_batch.astype(expected_dtype)

    # If resize_tensor_input(batch=1) succeeded at startup, FIXED_BATCH_SIZE
    # is 1 and img_batch (shape (1, H, W, C)) is used as-is. If the graph
    # couldn't be resized (some ops hardcode batch size), pad up to the
    # model's required fixed batch by repeating the single image, run
    # inference, and only keep the first result.
    if FIXED_BATCH_SIZE > img_batch.shape[0]:
        pad_count = FIXED_BATCH_SIZE - img_batch.shape[0]
        padding = np.repeat(img_batch[:1], pad_count, axis=0)
        img_batch = np.concatenate([img_batch, padding], axis=0)

    # Ensure a fresh, contiguous buffer -- reused/non-contiguous numpy
    # views can cause TFLite to read stale memory.
    img_batch = np.ascontiguousarray(img_batch)

    with INTERPRETER_LOCK:
        INTERPRETER.set_tensor(input_detail["index"], img_batch)
        INTERPRETER.invoke()
        output = INTERPRETER.get_tensor(OUTPUT_DETAILS[0]["index"])

    # Only the first row corresponds to our actual image; the rest (if any)
    # is padding.
    return output[:1]


# -------------------------------
# Severity Detection
# -------------------------------

def get_severity_from_bytes(image_bytes: bytes):

    np_arr = np.frombuffer(
        image_bytes,
        np.uint8
    )

    img = cv2.imdecode(
        np_arr,
        cv2.IMREAD_COLOR
    )

    if img is None:
        return "Unknown", 0.0

    hsv = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2HSV
    )

    # Detect green leaf
    leaf_mask = cv2.inRange(
        hsv,
        np.array([25, 40, 40]),
        np.array([85, 255, 255])
    )

    # Detect dark infected area
    disease_mask = cv2.inRange(
        hsv,
        np.array([0, 0, 0]),
        np.array([180, 255, 80])
    )

    infected_mask = cv2.bitwise_and(
        disease_mask,
        leaf_mask
    )

    infected_area = np.count_nonzero(
        infected_mask
    )

    total_leaf_area = np.count_nonzero(
        leaf_mask
    )

    ratio = (
        infected_area / total_leaf_area * 100
        if total_leaf_area > 0 else 0
    )

    if ratio < 10:
        severity = "Mild"
    elif ratio < 30:
        severity = "Moderate"
    elif ratio < 50:
        severity = "Severe"
    elif ratio < 70:
        severity = "Critical"
    else:
        severity = "Devastating"
    return severity, round(ratio, 2)


# -------------------------------
# Health Check
# -------------------------------
@router.get("/ping")
async def ping():
    return {"message": "Prediction API is running"}


# -------------------------------
# Prediction Endpoint
# -------------------------------
@router.post("/")
async def predict(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()

        image = read_file_as_image(image_bytes)

        img_batch = np.expand_dims(
            image,
            axis=0
        )

        predictions = run_tflite_inference(img_batch)

        predicted_class = CLASS_NAMES[
            np.argmax(predictions[0])
        ]

        confidence = float(
            np.max(predictions[0]) * 100
        )

        severity, infected_ratio = get_severity_from_bytes(
            image_bytes
        )

        # Healthy leaf override
        if predicted_class == "Healthy":
            severity = "No Infection"
            infected_ratio = 0.0

        return {
            "class": predicted_class,
            "confidence": round(confidence, 2),
            "severity": severity,
            "infected_ratio": infected_ratio
        }

    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Please try again with a valid leaf image."
        )