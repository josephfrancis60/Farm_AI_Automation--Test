import requests
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from services.logger_service import log_agent_action

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

    try:
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
    except Exception as e:
        return f"Weather API error: {e}"

def add_weather_history(location, temperature, rain_condition, humidity, timestamp=None):
    """
    Inserts a row into the WeatherHistory table.
    """
    from database.db_connection import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO WeatherHistory (Location, Temperature, Rain, Humidity, Timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        # Use current time if timestamp is None
        val_timestamp = timestamp if timestamp else datetime.now()
        
        cursor.execute(sql, (location, temperature, rain_condition, humidity, val_timestamp))
        conn.commit()
        return f"Successfully added weather history for {location}: {rain_condition}."
    except Exception as e:
        conn.rollback()
        return f"Error adding weather history: {e}"
    finally:
        conn.close()

def get_historical_weather(city="Kanija Bhavan", start_time=None, end_time=None):
    """
    Fetches historical weather data (simulated for recovery logic).
    Points are generated every hour during the downtime.
    """
    if not start_time or not end_time:
        return []

    log_agent_action(f"Generating historical weather recovery data for {city} from {start_time} to {end_time}")
    
    results = []
    current_check = start_time + timedelta(hours=1)
    # Ensure start_time is datetime
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time if '.' not in start_time else start_time.split('.')[0], '%Y-%m-%d %H:%M:%S')

    while current_check < end_time:
        results.append({
            "location": city,
            "timestamp": current_check,
            "temp": 24.5, 
            "condition": "Recorded during recovery",
            "humidity": 65
        })
        current_check += timedelta(hours=1)
        
    return results

def add_weather_history_batch(entries):
    """
    Bulk adds weather history records.
    """
    from database.db_connection import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO WeatherHistory (Location, Temperature, Rain, Humidity, Timestamp) VALUES (?, ?, ?, ?, ?)"
        data = [(e['location'], e['temp'], e['condition'], e['humidity'], e['timestamp']) for e in entries]
        cursor.executemany(sql, data)
        conn.commit()
        return len(entries)
    except Exception as e:
        conn.rollback()
        print(f"Error in batch weather insert: {e}")
        return 0
    finally:
        conn.close()

if __name__ == "__main__":
    load_dotenv()
    print(get_weather())