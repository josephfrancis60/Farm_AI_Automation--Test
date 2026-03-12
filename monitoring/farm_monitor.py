from database.db_connection import get_connection
from alerts.alert_manager import add_alert
from tools.irrigation_decision_tool import evaluate_irrigation_need
from tools.harvest_prediction_tool import predict_harvest_date
from services.logger_service import log_agent_action
from datetime import datetime, timedelta

def check_farm_status():
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
        
        # 1. Check Downtime
        check_system_downtime(cursor)

        # 2. Get all fields
        cursor.execute("SELECT FieldId, Crop FROM Fields")
        fields = cursor.fetchall()

        for field_id, crop in fields:
            print(f"  - Checking {crop} (Field {field_id})...")
            
            # Check Irrigation
            irrigation_res = evaluate_irrigation_need.invoke({"field_id": field_id})
            if isinstance(irrigation_res, dict):
                if irrigation_res["decision"] == "PROCEED":
                    add_alert("Irrigation Recommended", f"Field {field_id} ({crop}) needs watering. Reason: {irrigation_res['reason']}", "INFO")
            
            # Check Harvest
            harvest_res = predict_harvest_date.invoke({"field_id": field_id})
            if isinstance(harvest_res, dict):
                if harvest_res["status"] == "Approaching Harvest":
                    add_alert("Harvest Near", f"{crop} (Field {field_id}) is approaching harvest in {harvest_res['days_remaining']} days.", "WARNING")
                elif harvest_res["status"] == "Ready for Harvest":
                    add_alert("Ready to Harvest", f"{crop} (Field {field_id}) is ready! Expected harvest date was {harvest_res['expected_harvest_date']}.", "SUCCESS")

        # 3. Update LastRunTime
        cursor.execute("UPDATE SystemState SET LastRunTime = ? WHERE Id = 1", (datetime.now(),))
        conn.commit()
        print("DEBUG: Monitoring run completed.")

    except Exception as e:
        print(f"Error in farm monitor: {e}")
    finally:
        conn.close()

def check_system_downtime(cursor):
    """
    Checks if the system was offline and catches up on events.
    """
    cursor.execute("SELECT LastRunTime FROM SystemState WHERE Id = 1")
    row = cursor.fetchone()
    if not row:
        return

    last_run = row.LastRunTime
    downtime = datetime.now() - last_run
    
    if downtime > timedelta(minutes=5):
        minutes = int(downtime.total_seconds() / 60)
        print(f"  ! Downtime detected: {minutes} minutes.")
        add_alert("System Catch-up", f"System was offline for {minutes} minutes. Analyzing missed weather events...", "INFO")
        
        # Check if it rained during downtime
        cursor.execute("SELECT COUNT(*) FROM WeatherHistory WHERE Timestamp > ? AND Rain LIKE '%rain%'", (last_run,))
        rain_count = cursor.fetchone()[0]
        if rain_count > 0:
            add_alert("Downtime Rain Detected", f"It rained while the system was offline. Adjusting irrigation plans.", "WARNING")

if __name__ == "__main__":
    check_farm_status()
