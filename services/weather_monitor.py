from services.weather_service import get_weather
from database.db_connection import get_connection
from alerts.alert_manager import add_alert
from services.logger_service import log_agent_action
from datetime import datetime

def monitor_weather(city="Kanija Bhavan"):
    """
    Fetches latest weather and logs it to WeatherHistory.
    Generates alerts if significant rain or extreme heat is detected.
    """
    log_agent_action(f"Starting weather monitor check for {city}...")
    
    weather_data = get_weather(city)
    if isinstance(weather_data, str):
        log_agent_action(f"Error fetching weather: {weather_data}", "ERROR")
        return

    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        current = weather_data.get("current", {})
        temp = current.get("temperature")
        humidity = current.get("humidity")
        condition = current.get("condition", "")

        # Insert into History
        query = """
        INSERT INTO WeatherHistory (Timestamp, Location, Temperature, Rain, Humidity)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (datetime.now(), city, temp, condition, humidity))
        conn.commit()
        
        print(f"- Logged weather: {temp}°C, {condition}")

        # Basic alerting logic
        if "rain" in condition.lower() or "drizzle" in condition.lower():
            add_alert("Rain Detected", f"Current condition in {city}: {condition}. Check irrigation plans.", "WARNING")
        
        if temp > 35:
            add_alert("High Temperature Alert", f"It's {temp}°C in {city}. Crops might need extra water.", "WARNING")

    except Exception as e:
        print(f"Error in weather monitoring: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    monitor_weather()
