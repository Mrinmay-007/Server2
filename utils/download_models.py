# FILE_ID_1 = "1ZkCb3d7tmAdVR3Xc4OjcBvLJRsT2hXBo"
# FILE_ID_2 = "1ZWMqpAkhsbnuH-PatiJffqJqv9-Qk3FX"
# FILE_ID_3 = "1fDkGdHAccHWZa_J3aVQAJo29LXOzkSSn"
# FILE_ID_4 = "1emuuIncqZxerLdmoGWji_PsfBSTyGC8D"



# import os
# import gdown

# BASE_DIR = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "..")
# )

# MODEL_DIR = os.path.join(BASE_DIR, "ml_models")
# YOLO_DIR = os.path.join(MODEL_DIR, "yolo")

# os.makedirs(MODEL_DIR, exist_ok=True)
# os.makedirs(YOLO_DIR, exist_ok=True)

# FILE_ID_1 = "1ZkCb3d7tmAdVR3Xc4OjcBvLJRsT2hXBo"
# FILE_ID_2 = "1ZWMqpAkhsbnuH-PatiJffqJqv9-Qk3FX"
# FILE_ID_3 = "1fDkGdHAccHWZa_J3aVQAJo29LXOzkSSn"
# FILE_ID_4 = "1emuuIncqZxerLdmoGWji_PsfBSTyGC8D"

# FILES = {
#     "V1.keras": FILE_ID_1,
#     "detect_V2.keras": FILE_ID_2,
#     "yolo/best.pt": FILE_ID_3,
#     "yolo/best2.pt": FILE_ID_4
# }


# def download_models():
#     for file_name, file_id in FILES.items():
#         output_path = os.path.join(MODEL_DIR, file_name)

#         if not os.path.exists(output_path):
#             url = f"https://drive.google.com/uc?id={file_id}"
#             print(f"Downloading {file_name}...")
#             gdown.download(url, output_path, quiet=False) #type: ignore

#     print("All models downloaded.")

import os
import gdown

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

MODEL_DIR = os.path.join(BASE_DIR, "ml_models")
YOLO_DIR = os.path.join(MODEL_DIR, "yolo")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(YOLO_DIR, exist_ok=True)

FILES = {
    "V1.keras": "1ZkCb3d7tmAdVR3Xc4OjcBvLJRsT2hXBo",
    "detect_V2.keras": "1ZWMqpAkhsbnuH-PatiJffqJqv9-Qk3FX",
    "yolo/best.pt": "1fDkGdHAccHWZa_J3aVQAJo29LXOzkSSn",
    "yolo/best2.pt": "1emuuIncqZxerLdmoGWji_PsfBSTyGC8D"
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

        gdown.download(url, output_path, quiet=False)

    print("All models ready.")