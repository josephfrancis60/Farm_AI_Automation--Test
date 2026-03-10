from langchain.tools import tool

from tools.crop_tool import get_all_crops, add_crop, update_field, delete_field, get_field_id_by_crop
from tools.fertilizer_tool import get_fertilizer_recommendation
from tools.inventory_tool import check_fertilizer_stock, add_fertilizer, update_fertilizer_stock, delete_fertilizer
from tools.irrigation_tool import activate_sprinkler, get_irrigation_schedule, was_already_watered_today
from services.weather_service import get_weather
from datetime import datetime

@tool
def crops():
    """
    Get the list of all crops currently growing in the farm.
    Use this tool whenever you need to know which crops are available or to count them.
    """
    print("Tool: crops()")
    return get_all_crops()

@tool
def check_irrigation_status(city: str):
    """
    Check the irrigation schedule for today and compare with the weather forecast.
    Suggests whether to irrigate or skip based on rain forecast.
    
    Args:
        city: The city to check the weather for.
    """
    print(f"Tool: check_irrigation_status('{city}')")
    
    now = datetime.now()
    day_of_week = now.strftime('%A') # e.g., 'Monday'
    current_time = now.strftime('%H:%M')
    
    schedule = get_irrigation_schedule(day_of_week)
    if not schedule:
        return f"No irrigation is scheduled for today ({day_of_week})."
    
    weather_info = get_weather(city)
    rain_forecasted = False
    rain_details = ""
    
    if isinstance(weather_info, dict) and "forecast" in weather_info:
        for item in weather_info["forecast"]:
            if "rain" in item["condition"].lower() or "drizzle" in item["condition"].lower():
                rain_forecasted = True
                rain_details = f"Rain ({item['condition']}) is forecasted at {item['time']}."
                break
    
    report = f"Irrigation Schedule for {day_of_week}:\n"
    needs_action = []
    already_done = []
    
    for item in schedule:
        crop = item['crop']
        scheduled_time = item['time']
        duration = item['duration']
        
        # Link crop to field ID
        field_id = get_field_id_by_crop(crop)
        
        # Check if already watered today via IrrigationHistory
        if field_id and was_already_watered_today(field_id):
            already_done.append(crop)
            report += f"- {crop}: Already watered today. Skipping.\n"
            continue
        
        status = "Upcoming"
        if scheduled_time <= current_time:
            status = "Pending"
            
        report += f"- {crop}: Scheduled for {scheduled_time}, {duration} mins. Status: {status}\n"
        
        if field_id:
            needs_action.append({
                "field_id": field_id,
                "crop": crop,
                "duration": duration,
                "scheduled_time": scheduled_time
            })
            
    if rain_forecasted:
        report += f"\nRecommendation: SKIP irrigation. {rain_details}"
    elif not needs_action:
        if already_done:
            report += f"\nAll scheduled crops have already been watered today."
        else:
            report += "\nNo matching fields found in the farm layout for the scheduled crops."
    else:
        report += "\nRecommendation: PROCEED with irrigation. No rain is forecasted."
        report += "\nPlease confirm if I should start watering the scheduled crops."
        
    return report

@tool
def add_new_crop(crop: str, soil_type: str, area_acres: float):
    """
    Add a new crop to the farm fields.
    
    Args:
        crop: The name of the crop (e.g., 'Sugarcane').
        soil_type: The type of soil (e.g., 'Loamy', 'Sandy', 'Clay').
        area_acres: The area in acres.
    """
    print(f"Tool: add_new_crop('{crop}', '{soil_type}', {area_acres})")
    return add_crop(crop, soil_type, area_acres)

@tool
def update_existing_field(field_id: int, crop: str = None, soil_type: str = None, area_acres: float = None):
    """
    Update information for an existing field.
    
    Args:
        field_id: The ID of the field to update.
        crop: New crop name (optional).
        soil_type: New soil type (optional).
        area_acres: New area in acres (optional).
    """
    print(f"Tool: update_existing_field({field_id}, ...)")
    return update_field(field_id, crop, soil_type, area_acres)

@tool
def delete_crop_field(field_id: int):
    """
    Delete a crop field from the database.
    
    Args:
        field_id: The ID of the field to remove.
    """
    print(f"Tool: delete_crop_field({field_id})")
    return delete_field(field_id)

@tool
def fertilizer(crop_name: str):
    """
    Get fertilizer recommendation for a specific crop.
    
    Args:
        crop_name: The name of the crop to get recommendations for (e.g., 'Wheat', 'Corn').
    """
    print(f"Tool: fertilizer('{crop_name}')")
    return get_fertilizer_recommendation(crop_name)

@tool
def inventory():
    """
    Check the current stock of fertilizers in the inventory.
    Use this to see if we have enough fertilizer for the crops.
    """
    print("Tool: inventory()")
    return check_fertilizer_stock()

@tool
def add_inventory_item(fertilizer_name: str, stock_kg: float):
    """
    Add a new fertilizer to the inventory.
    
    Args:
        fertilizer_name: Name of the fertilizer.
        stock_kg: Initial amount in Kg.
    """
    print(f"Tool: add_inventory_item('{fertilizer_name}', {stock_kg})")
    return add_fertilizer(fertilizer_name, stock_kg)

@tool
def update_inventory_stock(fertilizer_name: str, stock_kg: float):
    """
    Update the stock amount of an existing fertilizer.
    
    Args:
        fertilizer_name: Name of the fertilizer.
        stock_kg: New amount in Kg.
    """
    print(f"Tool: update_inventory_stock('{fertilizer_name}', {stock_kg})")
    return update_fertilizer_stock(fertilizer_name, stock_kg)

@tool
def remove_from_inventory(fertilizer_name: str):
    """
    Delete a fertilizer item from the inventory.
    
    Args:
        fertilizer_name: Name of the fertilizer to remove.
    """
    print(f"Tool: remove_from_inventory('{fertilizer_name}')")
    return delete_fertilizer(fertilizer_name)

@tool
def irrigation(field_id: int, duration_minutes: int):
    """
    Activate the sprinkler irrigation system for a specific field and record the history.
    
    Args:
        field_id: The ID of the field to irrigate.
        duration_minutes: Duration of watering in minutes.
    """
    print(f"Tool: irrigation({field_id}, {duration_minutes})")
    return activate_sprinkler(field_id, duration_minutes)

@tool
def weather(city: str):
    """
    Get current weather and a 12-hour forecast (at 3-hour intervals) for a specific city.
    Useful for checking current conditions and planning for upcoming rain or heat.
    
    Args:
        city: The name of the city to check the weather for. If the user doesn't specify a city, use 'Kanija Bhavan' as a default.
    """
    print(f"Tool: weather('{city}')")
    return get_weather(city)