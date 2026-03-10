from database.db_connection import get_connection
from datetime import datetime

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