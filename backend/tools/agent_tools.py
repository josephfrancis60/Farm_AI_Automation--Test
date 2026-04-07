from langchain.tools import tool

from tools.crop_tool import get_all_crops, add_crop, update_field, delete_field, get_field_id_by_crop
from tools.fertilizer_tool import get_fertilizer_recommendation
from tools.inventory_tool import check_fertilizer_stock, add_fertilizer, update_fertilizer_stock, delete_fertilizer
from tools.irrigation_tool import activate_sprinkler, get_irrigation_schedule, was_already_watered_today
from services.weather_service import get_weather, add_weather_history
from datetime import datetime, timedelta, timezone
from alerts.reminder_manager import add_reminder, clear_reminders as clear_all_reminders
from alerts.alert_manager import clear_alerts as clear_all_alerts
from tools.irrigation_mgmt_tool import get_crop_schedule, add_schedule_entry, clear_crop_schedule

@tool
def crops():
    """
    Get the list of all crops currently growing in the farm.
    Use this tool whenever you need to know which crops are available or to count them.
    """
    print("Tool: crops()")
    return get_all_crops()

@tool
def set_reminder(title: str, message: str, delay_minutes: float = 0.0):
    """
    Set a reminder for the user. This will be visible in the 'Reminders' section of the UI.
    Use this when the user asks to be reminded about something (e.g., 'remind me to send an SMS in 5 minutes').
    
    Args:
        title: A short, descriptive title for the reminder.
        message: The detailed content of the reminder.
        delay_minutes: Optional delay in minutes from now when the reminder should 'hit' and notify the user.
    """
    due_dt = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
    due_time_str = due_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print(f"Tool: set_reminder('{title}', '{message}', due={due_time_str})")
    return add_reminder(title, message, due_time=due_time_str)

@tool
def check_irrigation_status(city: str):
    """
    Check the irrigation schedule for today and compare with the weather forecast.
    Suggests whether to irrigate or skip based on rain forecast.
    
    Args:
        city: The city to check the weather for.
    """
    print(f"Tool: check_irrigation_status('{city}')")
    
    now = datetime.now(timezone.utc)
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
def irrigation(field_id: int, duration_minutes: int, delay_minutes: float = 0.0):
    """
    Activate or schedule the sprinkler irrigation system for a specific field and record the history.
    
    Args:
        field_id: The ID of the field to irrigate.
        duration_minutes: Duration of watering in minutes.
        delay_minutes: Delay in minutes before starting. MANDATORY: If the user says 'start after 2 minutes', set this to 2. If they say 'start now', set to 0.
    """
    print(f"Tool: irrigation({field_id}, {duration_minutes}, {delay_minutes})")
    return activate_sprinkler(field_id, duration_minutes, delay_minutes)

@tool
def update_weather_history(location: str, temperature: float, rain_condition: str, humidity: float):
    """
    Manually add a weather record to the WeatherHistory table.
    
    Args:
        location: The location name (e.g., 'Kanija Bhavan').
        temperature: The temperature in Celsius.
        rain_condition: The rain condition (e.g., 'Rainy', 'Light Rain', 'Stormy').
        humidity: The humidity percentage.
    """
    print(f"Tool: update_weather_history('{location}', {temperature}, '{rain_condition}', {humidity})")
    return add_weather_history(location, temperature, rain_condition, humidity)

@tool
def weather(city: str):
    """
    Get the current weather and forecast for a specific city.
    Args:
        city: City name (e.g., 'Kanija Bhavan').
    """
    print(f"Tool: weather('{city}')")
    return get_weather(city)

@tool
def manage_database_table(table_name: str, action: str, data: dict, condition: dict = None):
    """
    Perform INSERT, UPDATE, or DELETE operations on specific farm database tables.
    Supported tables: 'Fields', 'IrrigationSchedule', 'Inventory', 'WeatherHistory'.
    
    Args:
        table_name: The name of the table to modify.
        action: The action to perform ('INSERT', 'UPDATE', 'DELETE').
        data: A dictionary of column names and values for INSERT or UPDATE.
        condition: A dictionary of column names and values for the WHERE clause (required for UPDATE and DELETE).
    """
    allowed_tables = ['Fields', 'IrrigationSchedule', 'Inventory', 'WeatherHistory']
    if table_name not in allowed_tables:
        return f"Error: Table '{table_name}' is not accessible via this tool."
    
    print(f"Tool: manage_database_table('{table_name}', '{action}', {data}, condition={condition})")
    
    from database.db_connection import get_connection
    conn = get_connection()
    if not conn:
        return "Error: Could not connect to database."
    
    cursor = conn.cursor()
    try:
        if action.upper() == 'INSERT':
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            values = list(data.values())
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)
            
        elif action.upper() == 'UPDATE':
            if not condition:
                return "Error: UPDATE requires a condition."
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            where_clause = " AND ".join([f"{k} = ?" for k in condition.keys()])
            values = list(data.values()) + list(condition.values())
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            cursor.execute(query, values)
            
        elif action.upper() == 'DELETE':
            if not condition:
                return "Error: DELETE requires a condition."
            where_clause = " AND ".join([f"{k} = ?" for k in condition.keys()])
            values = list(condition.values())
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            cursor.execute(query, values)
        else:
            return f"Error: Unsupported action '{action}'."
        
        affected = cursor.rowcount
        conn.commit()
        return f"Successfully performed {action} on {table_name}. Rows affected: {affected}."
        
    except Exception as e:
        conn.rollback()
        return f"Database error: {e}"
    finally:
        conn.close()

@tool
def clear_alerts():
    """
    Clear all active alerts from the system UI.
    Use this when the user explicitly asks to 'clear all alerts'.
    """
    print("Tool: clear_alerts()")
    clear_all_alerts()
    return "All alerts have been cleared."

@tool
def clear_reminders():
    """
    Clear all active reminders from the system UI.
    Use this when the user explicitly asks to 'clear all reminders'.
    """
    print("Tool: clear_reminders()")
    clear_all_reminders()
    return "All reminders have been cleared."

@tool
def get_irrigation_schedule_for_crop(crop_name: str):
    """
    Check the irrigation schedule for a specific crop.
    Use this when a new crop is added to see if it already has a schedule.
    """
    print(f"Tool: get_irrigation_schedule_for_crop('{crop_name}')")
    schedule = get_crop_schedule(crop_name)
    if not schedule:
        return f"No irrigation schedule found for {crop_name}."
    
    res = f"Irrigation schedule for {crop_name}:\n"
    for s in schedule:
        res += f"- {s['day']} at {s['time']} for {s['duration']} mins\n"
    return res

@tool
def add_irrigation_schedule(crop_name: str, day_of_week: str, time_of_day: str, duration_minutes: int):
    """
    Add a new irrigation schedule entry for a crop.
    Args:
        crop_name: The name of the crop.
        day_of_week: Day of the week (e.g., 'Monday').
        time_of_day: Time in 24h format (e.g., '08:00').
        duration_minutes: Duration in minutes.
    """
    print(f"Tool: add_irrigation_schedule('{crop_name}', '{day_of_week}', '{time_of_day}', {duration_minutes})")
    return add_schedule_entry(crop_name, day_of_week, time_of_day, duration_minutes)

@tool
def remove_irrigation_schedule(crop_name: str):
    """
    Remove all irrigation schedule entries for a specific crop.
    """
    print(f"Tool: remove_irrigation_schedule('{crop_name}')")
    success = clear_crop_schedule(crop_name)
    if success:
        return f"Successfully removed irrigation schedule for {crop_name}."
    return f"No irrigation schedule found to remove for {crop_name}."

@tool
def get_irrigation_history(crop_name: str = None, limit: int = 5):
    """
    Retrieve the recent irrigation history for the farm or a specific crop.
    Use this to answer questions like 'when was the last time I watered?' or 'how long have I watered my crops?'.
    
    Args:
        crop_name: Optional name of the crop to filter history for.
        limit: Number of recent records to retrieve (default is 5).
    """
    print(f"Tool: get_irrigation_history(crop_name='{crop_name}', limit={limit})")
    
    from database.db_connection import get_connection
    conn = get_connection()
    if not conn:
        return "I'm sorry, I couldn't connect to the records right now."
    
    cursor = conn.cursor()
    try:
        query = """
            SELECT F.Crop, H.DurationMinutes, H.ActivatedAt 
            FROM IrrigationHistory H
            JOIN Fields F ON H.FieldId = F.FieldId
        """
        params = []
        if crop_name:
            query += " WHERE F.Crop LIKE ?"
            params.append(f"%{crop_name}%")
        
        query += " ORDER BY H.ActivatedAt DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return f"I couldn't find any recent irrigation records{f' for {crop_name}' if crop_name else ''}."
        
        history_text = f"Recent irrigation history:\n"
        for row in rows:
            # Format time nicely
            try:
                dt = datetime.fromisoformat(row.ActivatedAt.replace(' ', 'T')) if isinstance(row.ActivatedAt, str) else row.ActivatedAt
                time_str = dt.strftime("%A, %b %d at %H:%M")
            except:
                time_str = str(row.ActivatedAt)
            history_text += f"- {row.Crop}: Watered for {row.DurationMinutes} minutes on {time_str}.\n"
        
        return history_text
        
    except Exception as e:
        return f"I encountered an error while looking up the history: {e}"
    finally:
        conn.close()