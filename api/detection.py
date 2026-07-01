
from fastapi import APIRouter, UploadFile, File, HTTPException
from ultralytics import YOLO
from concurrent.futures import ThreadPoolExecutor

import tensorflow as tf
import numpy as np

from PIL import Image

import tempfile
import shutil
import os

# --------------------------------------------------
# TensorFlow Optimization
# --------------------------------------------------
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "1"

# --------------------------------------------------
# Router
# --------------------------------------------------
router = APIRouter(
    prefix="/detect",
    tags=["Detection"]
)

# --------------------------------------------------
# Paths
# --------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

YOLO_MODEL_1 = os.path.join(
    PROJECT_ROOT,
    "ml_models",
    "yolo",
    "best.pt"
)

YOLO_MODEL_2 = os.path.join(
    PROJECT_ROOT,
    "ml_models",
    "yolo",
    "best2.pt"
)

KERAS_MODEL = os.path.join(
    PROJECT_ROOT,
    "ml_models",
    "detect_V2.keras"
)

CLASS_NAMES = [
    "Not Potato",
    "Potato"
]

# --------------------------------------------------
# Validate Model Files
# --------------------------------------------------
for model_path in (
    YOLO_MODEL_1,
    YOLO_MODEL_2,
    KERAS_MODEL
):
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

# --------------------------------------------------
# Load Models Once
# --------------------------------------------------
print("Loading YOLO Model 1...")
YOLO1 = YOLO(YOLO_MODEL_1)

print("Loading YOLO Model 2...")
YOLO2 = YOLO(YOLO_MODEL_2)

print("Loading Keras Model...")
KERAS = tf.keras.models.load_model(
    KERAS_MODEL,
    compile=False
)

print("All models loaded successfully.")

# --------------------------------------------------
# Thread Pool
# --------------------------------------------------
EXECUTOR = ThreadPoolExecutor(
    max_workers=2
)

# --------------------------------------------------
# Image Preprocessing
# --------------------------------------------------
def preprocess_image(
    image_path: str,
    target_size=(224, 224)
):
    image = (
        Image.open(image_path)
        .convert("RGB")
        .resize(target_size)
    )

    image = np.array(
        image,
        dtype=np.float32
    )

    image /= 255.0

    image = np.expand_dims(
        image,
        axis=0
    )

    return image

# --------------------------------------------------
# Health Check
# --------------------------------------------------
@router.get("/ping")
async def ping():
    return {
        "status": "ok",
        "models_loaded": True
    }

# --------------------------------------------------
# Detection Endpoint
# --------------------------------------------------
@router.post("/")
async def detect(
    file: UploadFile = File(...)
):

    temp_path = None

    try:

        suffix = (
            os.path.splitext(
                file.filename or ""
            )[1]
            or ".jpg"
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as tmp:

            shutil.copyfileobj(
                file.file,
                tmp
            )

            temp_path = tmp.name

        # ----------------------------------
        # YOLO Parallel Prediction
        # ----------------------------------
        future1 = EXECUTOR.submit(
            YOLO1.predict,
            temp_path,
            verbose=False
        )

        future2 = EXECUTOR.submit(
            YOLO2.predict,
            temp_path,
            verbose=False
        )

        result1 = future1.result()
        result2 = future2.result()

        # ----------------------------------
        # TensorFlow Prediction
        # ----------------------------------
        image = preprocess_image(
            temp_path
        )

        result3 = KERAS.predict(
            image,
            verbose=0
        )

        # ----------------------------------
        # YOLO 1
        # ----------------------------------
        class1 = result1[0].names[
            result1[0].probs.top1
        ]

        conf1 = float(
            result1[0].probs.top1conf
        )

        vote1 = (
            class1.lower()
            == "potato"
        )

        # ----------------------------------
        # YOLO 2
        # ----------------------------------
        class2 = result2[0].names[
            result2[0].probs.top1
        ]

        conf2 = float(
            result2[0].probs.top1conf
        )

        vote2 = (
            class2.lower()
            == "potato"
        )

        # ----------------------------------
        # TensorFlow
        # ----------------------------------
        class3 = CLASS_NAMES[
            np.argmax(result3[0])
        ]

        conf3 = float(
            np.max(result3[0])
        )

        vote3 = (
            class3.lower()
            == "potato"
        )

        # ----------------------------------
        # Majority Voting
        # ----------------------------------
        votes = [
            vote1,
            vote2,
            vote3
        ]

        final_decision = (
            "Potato"
            if votes.count(True) >= 2
            else "Not Potato"
        )

        avg_confidence = round(
            (
                conf1 +
                conf2 +
                conf3
            ) / 3 * 100,
            2
        )

        return {
            "final_decision": final_decision,
            "confidence": avg_confidence,
            "model_predictions": {
                "yolo_1": {
                    "class": class1,
                    "confidence": round(
                        conf1 * 100,
                        2
                    )
                },
                "yolo_2": {
                    "class": class2,
                    "confidence": round(
                        conf2 * 100,
                        2
                    )
                },
                "keras": {
                    "class": class3,
                    "confidence": round(
                        conf3 * 100,
                        2
                    )
                }
            }
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):
            os.remove(temp_path)

