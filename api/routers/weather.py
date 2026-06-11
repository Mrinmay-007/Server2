
import platform
import requests

import os
from fastapi import HTTPException, APIRouter
import datetime as dt
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")


# ---------- IP-based location ----------
def get_location_ip():
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        data = resp.json()
        lat, lon = map(float, data["loc"].split(","))
        return lat, lon
    except Exception as e:
        print("IP-based location failed:", e)
        return None, None

# ---------- GPS-based location (Android only) ----------
def get_location_android_gps():
    try:
        from plyer import gps  # type: ignore
        coords = {}

        def gps_callback(lat, lon):
            coords["lat"] = lat
            coords["lon"] = lon
            gps.stop()

        gps.configure(on_location=gps_callback)
        gps.start()

        import time
        for _ in range(20):  # wait max ~10s
            if "lat" in coords:
                return coords["lat"], coords["lon"]
            time.sleep(0.5)

    except Exception as e:
        print("Android GPS failed:", e)

    return None, None

# ---------- Unified function ----------
def get_device_location():
    system = platform.system()

    if system == "Windows":
        return get_location_ip()

    elif system == "Linux":  # Android usually reports "Linux"
        lat, lon = get_location_android_gps()
        if lat and lon:
            return lat, lon
        else:
            return get_location_ip()

    return get_location_ip()


# ---------- FastAPI Router ----------

import math

def dew_point(temp_c: float, humidity: float) -> float:
    """
    Calculate dew point (°C) given temperature (°C) and relative humidity (%).
    """
    a, b = 17.27, 237.7
    gamma = (a * temp_c) / (b + temp_c) + math.log(humidity / 100.0)
    dp = (b * gamma) / (a - gamma)
    return round(dp, 2)

def weather():
   
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Weather API key not configured")

    lat, lon = get_device_location()
    if not lat or not lon:
        raise HTTPException(status_code=400, detail="Could not determine location")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        weather =resp.json()
        
        timestamp = str(dt.datetime.utcfromtimestamp(weather['dt'])) # yy/mm/dd  hh/mm/ss
        dew =dew_point(weather["main"]["temp"],weather["main"]['humidity'])
        data ={
            'City':weather['name'],
            "Timestamp" :timestamp,
            "Weather": weather["weather"][0]["description"],
            "Temperature": str(weather["main"]["temp"]) + " °C",
            "Humidity": str(weather["main"]['humidity']) +" %",
            "Feels Like": str(weather['main']['feels_like'])+" °C",
            "Dew Point":str(dew) + ' °C',
            "Pressure":weather["main"]['pressure'] ,
            "Wind Speed":str(weather['wind']['speed'])+" m/s",
            "Cloudy":str(weather['clouds']['all'])+' %',
            "Visibility": str(round((weather['visibility']/1000 ),2)) +' Km'
        }
        return data
    
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {e}")

router = APIRouter(
    prefix="/weather",
    tags=["Weather"]
)
# /weather/current
@router.get("/current")
async def get_weather():
   data = weather()
   return data

# /weather/compatible
@router.get("/compatible")
async def get_compatible_weather(leaf: str):
    data = weather()

    
    temp = float(data["Temperature"].split()[0])       
    humidity = float(data["Humidity"].replace("%", ""))  
    weather_desc = data["Weather"].lower()

    # Default
    suitability = "Moderate"
    risk = "Medium"

    #  Potato growth suitability 
    if 18 <= temp <= 25 and 60 <= humidity <= 80:
        suitability = "Suitable"
        risk = "Low"
    elif (temp < 15 or temp > 30) or (humidity < 50 or humidity > 90):
        suitability = "Unsuitable"
        risk = "High"
    else:
        suitability = "Moderate"
        risk = "Medium"

    # ✅ Disease-specific weather 
    disease_risk = ""
    if leaf.lower() == "healthy":
        disease_risk = "No visible disease, keep monitoring."
    elif leaf.lower() == "early blight":
        if humidity > 80 and temp > 25:
            risk = "High"
            disease_risk = "High risk of spread due to humid & warm weather."
        else:
            disease_risk = "Moderate risk, monitor closely."
    elif leaf.lower() == "late blight":
        if humidity > 85 and 15 <= temp <= 25:
            risk = "Very High"
            disease_risk = "Late blight can spread rapidly in cool & humid conditions."
        else:
            disease_risk = "Moderate risk depending on field conditions."

    return {
        "City": data["City"],
        "Timestamp": data["Timestamp"],
        "Weather": data["Weather"],
        "Temperature": data["Temperature"],
        "Humidity": data["Humidity"],
        "Potato Suitability": suitability,
        "Risk Level": risk,
        "Disease Analysis": disease_risk
    }



# {
#   "City": "Kolkata",
#   "Timestamp": "2025-09-19 17:56:03",
#   "Weather": "haze",
#   "Temperature": "29.97 °C",
#   "Humidity": "89 %",
#   "Feels Like": "36.97 °C",
#   "Dew Point": "27.95 °C",
#   "Pressure": 1006,
#   "Wind Speed": "2.06 m/s",
#   "Cloudy": "40 %",
#   "Visibility": "3.2 Km"
# }