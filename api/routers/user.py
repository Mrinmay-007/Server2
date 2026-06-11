# =========================================
# user.py
# =========================================

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr
from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo import ReturnDocument   

from ...db import get_db
from ..auth.hashing import Hash   

import random
import string

router = APIRouter(
    prefix="/user",
    tags=["Users"]
)


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    pin: str
    role: str | None = "user"


def key_generator():
    characters = string.ascii_letters + string.digits

    random_string = ''.join(
        random.choices(characters, k=10)
    )

    return random_string


@router.get("/testing")
async def root():
    return {"message": "Hello, MongoDB + FastAPI"}


@router.post("/")
async def create_user(
    user: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):

    existing_user = await db["users"].find_one({
        "email": user.email
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

   
    counter = await db["counters"].find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    seq_number = counter["seq"]

    user_id = f"UR{seq_number:03d}"

    india_time = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    user_data = {

        "user_id": user_id,
        "name": user.name,
        "email": user.email,

        #  hashed pin
        "pin": Hash.bcrypt(user.pin),
        "role": user.role,

        "created_date": india_time.strftime("%d-%m-%Y"),
        "created_time": india_time.strftime("%I:%M:%S %p"),

        "created_at": india_time
    }

    result = await db["users"].insert_one(
        user_data
    )

    return {
        "message": "User created successfully",
        "id": str(result.inserted_id),
        "user_id": user_id
    }


@router.get("/")
async def get_users(
    db: AsyncIOMotorDatabase = Depends(get_db)
):

    users = []
    cursor = db["users"].find({})

    async for user in cursor:
        user["_id"] = str(user["_id"])
        # hide pin
        user.pop("pin", None)
        users.append(user)

    return users


@router.post("/login")
async def login_user(
    email: str,
    pin: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):

    user = await db["users"].find_one({
        "email": email
    })

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or pin"
        )

    # FIXED -> verify hashed pin
    is_valid = Hash.verify(
        pin,
        user["pin"]
    )

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or pin"
        )

    user["_id"] = str(user["_id"])

    return {
        "message": "Login successful",
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_date": user["created_date"],
        "created_time": user["created_time"]
    }


@router.delete("/{id}")
async def delete_user(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):

    result = await db["users"].delete_one({
        "user_id": id
    })

    if result.deleted_count == 1:
        return {
            "message": "User deleted successfully"}

    return {"message": "User not found"}