

# from fastapi import File, UploadFile , APIRouter
# import numpy as np
# from io import BytesIO
# from PIL import Image
# import tensorflow as tf
# import os
# import logging
# import cv2

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter(
#     prefix="/predict",
#     tags=["Prediction"],
# )
# #  -------------------------------
# #  Define Model Path
# # -------------------------------

# BASE_DIR = os.path.dirname(
#     os.path.dirname(
#         os.path.abspath(__file__)
#     )
# )

# MODEL_PATH = os.path.join(
#     BASE_DIR,
#     "ml_models",
#     "V1.keras"
# )

# # -------------------------------
# # Validate Model
# # -------------------------------
# if not os.path.exists(MODEL_PATH):
#     raise FileNotFoundError(
#         f"Model not found: {MODEL_PATH}"
#     )

# # -------------------------------
# # Load Model Once
# # -------------------------------
# logger.info("Loading disease model...")

# MODEL = tf.keras.models.load_model(
#     MODEL_PATH,
#     compile=False
# )

# logger.info("Disease model loaded.")
# CLASS_NAMES = ["Early Blight", "Late Blight", "Healthy"]



# # -------------------------------
# # Severity Detection
# # -------------------------------
# def get_severity_from_bytes(
#     image_bytes: bytes
# ):

#     np_arr = np.frombuffer(
#         image_bytes,
#         np.uint8
#     )

#     img = cv2.imdecode(
#         np_arr,
#         cv2.IMREAD_COLOR
#     )

#     if img is None:
#         return "Unknown", 0.0

#     hsv = cv2.cvtColor(
#         img,
#         cv2.COLOR_BGR2HSV
#     )

#     leaf_mask = cv2.inRange(
#         hsv,
#         np.array([25, 40, 40]),
#         np.array([85, 255, 255])
#     )

#     disease_mask = cv2.inRange(
#         hsv,
#         np.array([0, 0, 0]),
#         np.array([180, 255, 80])
#     )

#     infected_mask = cv2.bitwise_and(
#         disease_mask,
#         leaf_mask
#     )

#     infected_area = np.count_nonzero(
#         infected_mask
#     )

#     total_leaf_area = np.count_nonzero(
#         leaf_mask
#     )

#     ratio = (
#         infected_area /
#         total_leaf_area *
#         100
#         if total_leaf_area > 0
#         else 0
#     )

#     if ratio < 10:
#         severity = "Mild"
#     elif ratio < 30:
#         severity = "Moderate"
#     else:
#         severity = "Severe"

#     return severity, ratio


# # -------------------------------
# # API Endpoints
# # -------------------------------

# @router.get("/ping")
# async def ping():
#     return "Hello, I am alive"

# def read_file_as_image(data) -> np.ndarray:
#     image = np.array(Image.open(BytesIO(data)))
#     return image

# @router.post("/")
# async def predict(
#     file: UploadFile = File(...)
# ):
#     image = read_file_as_image(await file.read())
#     img_batch = np.expand_dims(image, 0)
    
#     predictions = MODEL.predict(img_batch)

#     predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
#     confidence = np.max(predictions[0])
#     return {
#         'class': predicted_class,
#         'confidence': float(confidence)
#     }


from fastapi import File, UploadFile, APIRouter, HTTPException
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf
import os
import logging
import cv2

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
    "V1.keras"
)

# -------------------------------
# Validate Model Path
# -------------------------------
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

# -------------------------------
# Load Model
# -------------------------------
logger.info("Loading disease model...")

MODEL = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False
)

logger.info("Disease model loaded successfully.")

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

        predictions = MODEL.predict(img_batch)

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
        logger.error(str(e))
        raise HTTPException(
            status_code=500,
            detail="Prediction failed"
        )