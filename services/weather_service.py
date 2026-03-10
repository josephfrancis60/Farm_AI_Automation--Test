import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city="London, GB"):
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
    
    return result