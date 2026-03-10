from database.db_connection import get_connection
from datetime import datetime, date

def activate_sprinkler(field_id, duration_minutes):
    conn = get_connection()
    cursor = conn.cursor()

    # Record in history
    query = "INSERT INTO IrrigationHistory (FieldId, DurationMinutes, ActivatedAt) VALUES (?, ?, ?)"
    cursor.execute(query, (field_id, duration_minutes, datetime.now()))
    
    conn.commit()
    conn.close()

    return (
        f"Irrigation Decision:\n"
        f"Sprinkler system activated for field ID {field_id}.\n"
        f"Duration: {duration_minutes} minutes.\n"
        f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Transaction recorded in database."
    )

def was_already_watered_today(field_id):
    """
    Check if a field was already irrigated today by querying IrrigationHistory.
    Returns True if irrigated today, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().strftime('%Y-%m-%d')
    query = (
        "SELECT COUNT(*) FROM IrrigationHistory "
        "WHERE FieldId = ? AND CAST(ActivatedAt AS DATE) = ?"
    )
    cursor.execute(query, (field_id, today))
    count = cursor.fetchone()[0]
    conn.close()

    return count > 0

def get_irrigation_schedule(day_of_week):
    """
    Fetch the irrigation schedule for a specific day of the week.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT Crop, DayOfWeek, TimeOfDay, DurationMinutes FROM IrrigationSchedule WHERE DayOfWeek = ?"
    cursor.execute(query, (day_of_week,))
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    schedule = []
    for row in rows:
        schedule.append({
            "crop": row.Crop,
            "day": row.DayOfWeek,
            "time": row.TimeOfDay,
            "duration": row.DurationMinutes
        })
    
    return schedule