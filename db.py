import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = "Project"



class Database:
    client: Optional[AsyncIOMotorClient] = None 

db_instance = Database()

async def get_db():
    if db_instance.client is None:
        raise RuntimeError("Database client is not connected.")
    return db_instance.client[DATABASE_NAME]

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient(MONGO_URL)
    print("✅ Connected to MongoDB")

async def close_mongo_connection():
    if db_instance.client is not None:
        db_instance.client.close()


