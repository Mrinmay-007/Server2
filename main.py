

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn


# from utils.download_models import download_models
# from api import prediction, detection

# app = FastAPI()
# # ============================
# # Download models first
# # ============================
# @app.on_event("startup")
# async def startup():
#     download_models()


# # ============================
# # FastAPI app
# # ============================

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ============================
# # Include Routers
# # ============================
# app.include_router(prediction.router)
# app.include_router(detection.router)

# # ============================
# # Run App
# # ============================
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="localhost",
#         port=8000,
#         reload=True
#     )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from utils.download_models import download_models

app = FastAPI()


# ============================
# Startup Event
# ============================
@app.on_event("startup")
async def startup():
    # Download models first
    download_models()

    # Import routers after models exist
    from api import prediction, detection

    app.include_router(prediction.router)
    app.include_router(detection.router)


# ============================
# Middleware
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# Root route
# ============================
@app.get("/")
def root():
    return {"message": "API Running"}


# ============================
# Run App
# ============================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000
    )