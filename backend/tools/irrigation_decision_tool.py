from langchain.tools import tool
from database.db_connection import get_connection
from datetime import datetime, timedelta

@tool
def evaluate_irrigation_need(field_id: int):
    """
    Evaluates whether a specific field needs irrigation based on 
    past weather, soil type, and current schedule.
    """
    print(f"Tool: evaluate_irrigation_need({field_id})")
    conn = get_connection()
    if not conn:
        return "Database connection failed."

    try:
        cursor = conn.cursor()

        # 1. Get Field Info
        cursor.execute("SELECT Crop, SoilType, Area FROM Fields WHERE FieldId = ?", (field_id,))
        field = cursor.fetchone()
        if not field:
            return f"Field ID {field_id} not found."
        
        crop, soil, area = field

        # 2. Get Recent Weather (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("SELECT Rain FROM WeatherHistory WHERE Timestamp > ?", (yesterday,))
        history = cursor.fetchall()
        
        recent_rain = any("rain" in str(row[0]).lower() for row in history)

        # 3. Check if already watered today
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) FROM IrrigationHistory WHERE FieldId = ? AND CAST(ActivatedAt AS DATE) = ?", (field_id, today))
        already_watered = cursor.fetchone()[0] > 0

        # Decision Logic
        decision = "PROCEED"
        reason = "Soil moisture might be low and no rain detected."

        if already_watered:
            decision = "SKIP"
            reason = "Already watered today."
        elif recent_rain:
            decision = "DELAY"
            reason = "Rain detected in the last 24 hours. Soil is likely moist."
        
        # Soil specific adjustments
        if soil.lower() == 'sandy' and decision == "DELAY":
            decision = "PROCEED"
            reason = "Rain detected, but sandy soil drains fast. Suggest light irrigation."

        return {
            "field_id": field_id,
            "crop": crop,
            "soil": soil,
            "decision": decision,
            "reason": reason,
            "recent_rain": recent_rain,
            "already_watered_today": already_watered
        }

    except Exception as e:
        return f"Error evaluating irrigation: {e}"
    finally:
        conn.close()
