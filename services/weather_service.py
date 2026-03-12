import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Simple global cache to strictly enforce 30-minute interval
_weather_cache = {}

def get_weather(city="Kanija Bhavan"):
    now = time.time()
    # Respect 30-minute interval (1800 seconds)
    if city in _weather_cache:
        last_time, last_data = _weather_cache[city]
        if now - last_time < 1800:
            return last_data

    # Current weather
    current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    # 5-day forecast
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    current_response = requests.get(current_url)
    forecast_response = requests.get(forecast_url)

    if current_response.status_code != 200:
        return "Unable to fetch current weather data."

    current_data = current_response.json()
    
    result = {
        "current": {
            "temperature": current_data["main"]["temp"],
            "humidity": current_data["main"]["humidity"],
            "condition": current_data["weather"][0]["description"]
        }
    }

    if forecast_response.status_code == 200:
        forecast_data = forecast_response.json()
        # Get next 4 forecast points (approx. 12 hours)
        result["forecast"] = [
            {
                "time": item["dt_txt"],
                "condition": item["weather"][0]["description"],
                "temp": item["main"]["temp"]
            }
            for item in forecast_data["list"][:4]
        ]
    
    # Update cache
    _weather_cache[city] = (time.time(), result)
    
    return result