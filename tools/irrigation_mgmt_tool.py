from database.db_connection import get_connection

def get_crop_schedule(crop_name):
    """
    Returns all irrigation schedule entries for a given crop.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT DayOfWeek, TimeOfDay, DurationMinutes FROM IrrigationSchedule WHERE LOWER(Crop) = LOWER(?)"
    cursor.execute(query, (crop_name,))
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    schedule = []
    for row in rows:
        schedule.append({
            "day": row.DayOfWeek,
            "time": row.TimeOfDay,
            "duration": row.DurationMinutes
        })
    
    return schedule

def add_schedule_entry(crop_name, day_of_week, time_of_day, duration_minutes):
    """
    Adds a new irrigation schedule entry for a crop.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "INSERT INTO IrrigationSchedule (Crop, DayOfWeek, TimeOfDay, DurationMinutes) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (crop_name, day_of_week, time_of_day, duration_minutes))
    
    conn.commit()
    conn.close()
    return f"Successfully added irrigation schedule for {crop_name} on {day_of_week} at {time_of_day} for {duration_minutes} minutes."

def clear_crop_schedule(crop_name):
    """
    Removes all irrigation schedule entries for a specific crop.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "DELETE FROM IrrigationSchedule WHERE LOWER(Crop) = LOWER(?)"
    cursor.execute(query, (crop_name,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0
