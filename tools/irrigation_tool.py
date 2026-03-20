import os
import threading
from twilio.rest import Client
from database.db_connection import get_connection
from datetime import datetime, date
from services.logger_service import log_interaction
import json

def _execute_irrigation(field_id, duration_minutes, crop_name):
    """
    Internal function to execute the database records and SMS.
    """
    print(f"DEBUG: Executing irrigation for {crop_name} NOW...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Record in history
        query = "INSERT INTO IrrigationHistory (FieldId, DurationMinutes, ActivatedAt) VALUES (?, ?, ?)"
        cursor.execute(query, (field_id, duration_minutes, datetime.now()))
        
        conn.commit()
    except Exception as e:
        print(f"Database error during irrigation execution: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    # Send SMS via Twilio
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
    target_phone = os.environ.get('TARGET_PHONE_NUMBER')

    if account_sid and auth_token and account_sid != "your_account_sid_here":
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Sprinkler: turned on for {duration_minutes} minutes in field '{crop_name}'.",
                from_=twilio_phone,
                to=target_phone
            )
            log_interaction("SYSTEM", f"SMS notification sent to {target_phone} (SID: {message.sid}).")
        except Exception as e:
            log_interaction("SYSTEM", f"Failed to send SMS notification: {str(e)}", status="ERROR")
    else:
        log_interaction("SYSTEM", "Twilio credentials not configured. Irrigation SMS skipped.", status="WARNING")

    # Auto-clear related alerts
    alerts_file = "alerts/active_alerts.json"
    if os.path.exists(alerts_file):
        try:
            with open(alerts_file, "r") as f:
                alerts = json.load(f)
            
            # Filter out alerts that mention this field or crop
            field_str = f"field {field_id}"
            new_alerts = []
            for a in alerts:
                title = a.get("title", "").lower()
                msg = a.get("message", "").lower()
                if field_str in title or field_str in msg or crop_name.lower() in title or crop_name.lower() in msg:
                    continue
                new_alerts.append(a)
            
            if len(new_alerts) < len(alerts):
                with open(alerts_file, "w") as f:
                    json.dump(new_alerts, f, indent=4)
                print(f"DEBUG: Cleared {len(alerts) - len(new_alerts)} related alerts for {crop_name}.")
        except Exception as e:
            print(f"Error clearing alerts during irrigation: {e}")


def activate_sprinkler(field_id, duration_minutes, delay_minutes=0):
    """
    Activates the sprinkler for a given field and duration.
    If delay_minutes > 0, the activation is scheduled asynchronously.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch the Field Name (Crop) based on FieldId
    crop_name = f"Field {field_id}"
    cursor.execute("SELECT Crop FROM Fields WHERE FieldId = ?", (field_id,))
    row = cursor.fetchone()
    if row and row.Crop:
        crop_name = row.Crop
        
    conn.close()

    if delay_minutes > 0:
        # Schedule the execution asynchronously
        print(f"DEBUG: Scheduling irrigation for {crop_name} in {delay_minutes} minutes.")
        timer = threading.Timer(delay_minutes * 60.0, _execute_irrigation, args=[field_id, duration_minutes, crop_name])
        timer.start()
        return (
            f"Irrigation Decision:\n"
            f"Sprinkler system scheduled to activate for field '{crop_name}' in {delay_minutes} minutes.\n"
            f"Duration: {duration_minutes} minutes."
        )
    else:
        # Execute immediately
        _execute_irrigation(field_id, duration_minutes, crop_name)
        return (
            f"Irrigation Decision:\n"
            f"Sprinkler system activated for field '{crop_name}'.\n"
            f"Duration: {duration_minutes} minutes.\n"
            f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Transaction recorded in database and SMS sent (if configured)."
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