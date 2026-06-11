
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from zoneinfo import ZoneInfo
from ...db import get_db
from pydantic import BaseModel

router = APIRouter(
    prefix="/log",
    tags=["Logbook"]
)

class PredictionData(BaseModel):
    user_id: str
    predicted_class: str
    confidence: float
    severity: str
    ratio: float


@router.post("/save")
async def save_prediction(
    log: PredictionData,
    db: AsyncIOMotorDatabase = Depends(get_db)
):

    india_time = datetime.now(ZoneInfo("Asia/Kolkata"))

    prediction_data = {
        "user_id": log.user_id,
        "class": log.predicted_class,
        "confidence": log.confidence,
        "severity": log.severity,
        "infected_ratio": round(log.ratio, 2),

        "prediction_date": india_time.strftime("%d-%m-%Y"),
        "prediction_time": india_time.strftime("%I:%M:%S %p"),

        "created_at": india_time
    }
    result = await db["prediction"].insert_one(prediction_data)

    return {
        "message": "Prediction saved successfully",
        "id": str(result.inserted_id)
    }


@router.get("/history/{user_id}")
async def get_prediction_history(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    history = []
    cursor = db["prediction"].find({"user_id": user_id}).sort("prediction_date", -1).sort("prediction_time", -1)
    async for record in cursor:
        record["_id"] = str(record["_id"])
        history.append(record)
    return history

# ignore
@router.get("/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):

    total_predictions = await db["prediction"].count_documents(
        {"user_id": user_id}
    )

    # Disease-wise counts
    pipeline = [
        {
            "$match": {"user_id": user_id}
        },
        {
            "$group": {
                "_id": "$class",
                "count": {"$sum": 1}
            }
        }
    ]

    disease_stats = await db["prediction"].aggregate(pipeline).to_list(length=None)

    # Date-wise history
    history_pipeline = [
        {
            "$match": {"user_id": user_id}
        },
        {
            "$group": {
                "_id": "$prediction_date",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    history_data = await db["prediction"].aggregate(history_pipeline).to_list(length=None)

    return {
        "total_predictions": total_predictions,
        "disease_stats": disease_stats,
        "history_data": history_data
    }