

import os
import gdown

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

os.makedirs(MODEL_DIR, exist_ok=True)


FILES = {
    # "V1.keras": "1ZkCb3d7tmAdVR3Xc4OjcBvLJRsT2hXBo",
    "V1.tflite": "1bAS4jExLfP_8QOqZyv7a7lYuhfk0zcML",
    # "detect_V1.keras": "1-g3oha1BJ1kljQH-VMbx3XSqVJ500Ru6",
    "detect_V1.tflite": "1Jq11VisZ-A1rsLtRCmb9IjgIkzN8yGQw",
    
}


def download_models():
    for file_name, file_id in FILES.items():
        output_path = os.path.join(MODEL_DIR, file_name)

        # Skip if already exists
        if os.path.exists(output_path):
            print(f"{file_name} already exists. Skipping...")
            continue

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"Downloading {file_name}...")

        gdown.download(url, output_path, quiet=False) #type:ignore

    print("All models ready.")

