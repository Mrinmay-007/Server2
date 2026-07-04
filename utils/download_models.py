

import os
import gdown

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

MODEL_DIR = os.path.join(BASE_DIR, "ml_models")


os.makedirs(MODEL_DIR, exist_ok=True)
# os.makedirs(YOLO_DIR, exist_ok=True)

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

        gdown.download(url, output_path, quiet=False)

    print("All models ready.")


# import os
# import gdown
# import logging

# logger = logging.getLogger(__name__)

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

# os.makedirs(MODEL_DIR, exist_ok=True)
# # NOTE: the original code also had `os.makedirs(YOLO_DIR, exist_ok=True)` here,
# # but YOLO_DIR was never defined anywhere in the project. That line threw
# # NameError the instant this module was imported, which crashed the app
# # before it could even start -- this was the actual cause of the failed
# # deployment. Removed since no YOLO model is used anywhere in this codebase.

# FILES = {
#     # "V1.keras": "1ZkCb3d7tmAdVR3Xc4OjcBvLJRsT2hXBo",
#     "V1.tflite": "1bAS4jExLfP_8QOqZyv7a7lYuhfk0zcML",
#     # "detect_V1.keras": "1-g3oha1BJ1kljQH-VMbx3XSqVJ500Ru6",
#     "detect_V1.tflite": "1Jq11VisZ-A1rsLtRCmb9IjgIkzN8yGQw",
    
# }

# def download_models():
#     """
#     Downloads each model file from Google Drive if it doesn't already
#     exist locally. Validates the result so a corrupted/incomplete
#     download (e.g. Google Drive quota page instead of the real file)
#     fails loudly instead of silently leaving a broken model on disk.
#     """
#     for file_name, file_id in FILES.items():
#         output_path = os.path.join(MODEL_DIR, file_name)

#         if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
#             logger.info(f"{file_name} already exists ({os.path.getsize(output_path)} bytes). Skipping.")
#             continue

#         url = f"https://drive.google.com/uc?id={file_id}"
#         logger.info(f"Downloading {file_name} from Google Drive...")

#         try:
#             # fuzzy=True lets gdown resolve Drive's "can't scan for viruses"
#             # confirmation page automatically instead of saving that HTML
#             # page as if it were the model file.
#             gdown.download(url, output_path, quiet=False, fuzzy=True)
#         except Exception as e:
#             raise RuntimeError(
#                 f"Failed to download {file_name} from Google Drive (id={file_id}): {e}. "
#                 f"Check that the file is shared as 'Anyone with the link' and that "
#                 f"the cloud host can reach drive.google.com."
#             ) from e

#         if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
#             raise RuntimeError(
#                 f"Download of {file_name} appears to have failed or produced an "
#                 f"empty file. This usually means Google Drive returned a quota "
#                 f"or confirmation page instead of the actual file."
#             )

#         logger.info(f"Downloaded {file_name} successfully ({os.path.getsize(output_path)} bytes).")

#     logger.info("All models ready.")