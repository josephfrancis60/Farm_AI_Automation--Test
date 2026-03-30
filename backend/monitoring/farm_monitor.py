from database.db_connection import get_connection
from alerts.alert_manager import add_alert
from tools.irrigation_decision_tool import evaluate_irrigation_need
from tools.harvest_prediction_tool import predict_harvest_date
from services.logger_service import log_agent_action
from services.weather_service import get_historical_weather, add_weather_history_batch
from datetime import datetime, timedelta
from alerts.reminder_manager import add_reminder, get_active_reminders

def check_farm_status(skip_throttle=False):
    """
    Main monitoring loop. Checks all fields and generates proactive alerts.
    """
    log_agent_action("Starting proactive farm monitoring run...")
    
    conn = get_connection()
    if not conn:
        print("Error: Could not connect to database.")
        return

    try:
        cursor = conn.cursor()
        
        # 0. Throttling: Check if we just ran recently (less than 30 mins ago)
        cursor.execute("SELECT LastRunTime FROM SystemState WHERE Id = 1")
        row = cursor.fetchone()
        if row and row.LastRunTime and not skip_throttle:
            time_since_last_run = datetime.now() - row.LastRunTime
            if time_since_last_run < timedelta(minutes=30):
                print(f"DEBUG: Monitoring skipped. Last run was {int(time_since_last_run.total_seconds()/60)} mins ago (Threshold: 30 mins).")
                return

        # 1. Check Downtime
        check_system_downtime(cursor)

        # 2. Check upcoming irrigation schedules
        check_irrigation_alerts(cursor)

        # 3. Get all fields
        cursor.execute("SELECT FieldId, Crop FROM Fields")
        fields = cursor.fetchall()

        for field_id, crop in fields:
            print(f"  - Checking {crop} (Field {field_id})...")
            
            # Check Irrigation
            irrigation_res = evaluate_irrigation_need.invoke({"field_id": field_id})
            if isinstance(irrigation_res, dict):
                if irrigation_res["decision"] == "PROCEED":
                    add_alert("Irrigation Recommended", f"{crop} (Field {field_id}) needs watering. Reason: {irrigation_res['reason']}", "INFO")
            
            # Check Harvest
            harvest_res = predict_harvest_date.invoke({"field_id": field_id})
            if isinstance(harvest_res, dict):
                if harvest_res["status"] == "Approaching Harvest":
                    add_alert("Harvest Near", f"{crop} (Field {field_id}) is approaching harvest in {harvest_res['days_remaining']} days.", "WARNING")
                elif harvest_res["status"] == "Ready for Harvest":
                    add_alert("Ready to Harvest", f"{crop} (Field {field_id}) is ready! Expected harvest date was {harvest_res['expected_harvest_date']}.", "SUCCESS")

        # 4. Update LastRunTime
        cursor.execute("UPDATE SystemState SET LastRunTime = ? WHERE Id = 1", (datetime.now(),))
        conn.commit()
        print("DEBUG: Monitoring run completed.")

    except Exception as e:
        print(f"Error in farm monitor: {e}")
    finally:
        conn.close()

def check_system_downtime(cursor):
    """
    Checks if the system was offline and catches up on missed events.
    """
    from alerts.alert_manager import get_active_alerts, remove_alert

    cursor.execute("SELECT LastHeartbeat FROM SystemState WHERE Id = 1")
    row = cursor.fetchone()
    if not row or not row.LastHeartbeat:
        return

    last_heartbeat = row.LastHeartbeat
    now = datetime.now()
    downtime = now - last_heartbeat
    
    # Only process significant downtime ( > 2 mins)
    if downtime > timedelta(minutes=2):
        total_minutes = int(downtime.total_seconds() / 60)
        days = total_minutes // (24 * 60)
        remaining_minutes = total_minutes % (24 * 60)
        hours = remaining_minutes // 60
        mins = remaining_minutes % 60
        
        downtime_str = ""
        if days > 0:
            downtime_str += f"{days}d "
        if hours > 0 or days > 0:
            downtime_str += f"{hours}h "
        downtime_str += f"{mins}m"
        
        print(f"  ! Downtime detected: {downtime_str.strip()}.")
        
        # Clear existing "System Catch-up" alerts to avoid stale ones
        existing_alerts = get_active_alerts()
        for a in existing_alerts:
            if "System Catch-up" in a.get("title", ""):
                remove_alert(a["id"])
        
        add_alert("System Catch-up", f"System was offline for {downtime_str}. Fetching missed activities...", "INFO")
        
        # 1. Fetch and Log Missed Weather Events
        missed_weather = get_historical_weather(start_time=last_heartbeat, end_time=now)
        if missed_weather:
            count = add_weather_history_batch(missed_weather)
            print(f"  - Recovered {count} missed weather data points.")
        
        # 2. Check if it rained during downtime
        cursor.execute("SELECT COUNT(*) FROM WeatherHistory WHERE Timestamp > ? AND Rain LIKE '%rain%'", (last_heartbeat,))
        rain_count = cursor.fetchone()[0]
        if rain_count > 0:
            add_alert("Downtime Rain Detected", f"Rain was recorded during the {downtime_str} offline period. Irrigation plans updated.", "WARNING")

    # Update LastHeartbeat at the end of detection run
    cursor.execute("UPDATE SystemState SET LastHeartbeat = ? WHERE Id = 1", (datetime.now(),))

def check_irrigation_alerts(cursor):
    """
    Checks the IrrigationSchedule for entries in the next 35 minutes and sets reminders.
    """
    now = datetime.now()
    day_of_week = now.strftime('%A')
    
    # Check for schedules today
    cursor.execute("SELECT Crop, TimeOfDay, DurationMinutes FROM IrrigationSchedule WHERE DayOfWeek = ?", (day_of_week,))
    schedules = cursor.fetchall()
    
    if not schedules:
        return

    existing_reminders = get_active_reminders()
    
    for crop, time_str, duration in schedules:
        try:
            # Parse time (assumed format HH:MM)
            sched_hour, sched_min = map(int, time_str.split(':'))
            sched_time = now.replace(hour=sched_hour, minute=sched_min, second=0, microsecond=0)
            
            # If the scheduled time is in the past for today, skip unless it's within the next 35 mins (next day case handled by scheduler)
            # Actually, the scheduler runs every 30 mins, so we want to catch things in the NEXT 35 mins.
            
            time_diff = sched_time - now
            
            # Check 5-minute pre-alert (if scheduled time is between 5 and 35 minutes from now)
            if timedelta(minutes=5) <= time_diff <= timedelta(minutes=35):
                reminder_title = "Irrigation Starting Soon"
                reminder_msg = f"Irrigation for {crop} is scheduled to start in 5 minutes (at {time_str})."
                due_time = sched_time - timedelta(minutes=5)
                
                # Deduplicate: Don't add if a similar reminder exists for the same time
                if not any(r['title'] == reminder_title and r['due_time'].startswith(due_time.strftime("%Y-%m-%d %H:%M")) for r in existing_reminders):
                    add_reminder(reminder_title, reminder_msg, due_time.strftime("%Y-%m-%d %H:%M:%S"))
                    print(f"  - Proactive Reminder: {reminder_title} for {crop} at {time_str} (Alert at {due_time.strftime('%H:%M')})")

            # Check Start Alert (if scheduled time is between 0 and 30 minutes from now)
            if timedelta(minutes=0) <= time_diff <= timedelta(minutes=30):
                reminder_title = "Irrigation Starting NOW"
                reminder_msg = f"Irrigation for {crop} is starting now as per schedule ({time_str})."
                due_time = sched_time
                
                if not any(r['title'] == reminder_title and r['due_time'].startswith(due_time.strftime("%Y-%m-%d %H:%M")) for r in existing_reminders):
                    add_reminder(reminder_title, reminder_msg, due_time.strftime("%Y-%m-%d %H:%M:%S"))
                    print(f"  - Proactive Notification: {reminder_title} for {crop} at {time_str}")

        except Exception as e:
            print(f"Error parsing schedule for {crop}: {e}")

if __name__ == "__main__":
    check_farm_status()
