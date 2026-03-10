from services.weather_service import get_weather

def weather_tool(city="Kanija Bhavan"):

    weather = get_weather(city)

    if isinstance(weather, str):
        return weather

    return f"""
Weather in {city}

Temperature: {weather['temperature']}°C
Humidity: {weather['humidity']}%
Condition: {weather['condition']}
"""