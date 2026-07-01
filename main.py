

from fastapi import FastAPI  #type: ignore
from fastapi.middleware.cors import CORSMiddleware #type: ignore
import uvicorn #type: ignore
import os

# ============================
# from .db import connect_to_mongo, close_mongo_connection
from .api import prediction,detection


# ============================
app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
#  Database Connection
# ======================


# @app.on_event("startup")
# async def startup_event():
#     await connect_to_mongo()

# @app.on_event("shutdown")
# async def shutdown_event():
#     await close_mongo_connection()
    
# ======================
#  API Router
# ======================
 
app.include_router(prediction.router)
app.include_router(detection.router)


# ======================
# Main
# ======================

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
