from langchain.tools import tool
from database.db_connection import get_connection
from datetime import datetime, timedelta

@tool
def predict_harvest_date(field_id: int):
    """
    Predicts the harvest date for a field based on planting date 
    and crop growth data.
    """
    print(f"Tool: predict_harvest_date({field_id})")
    conn = get_connection()
    if not conn:
        return "Database connection failed."

    try:
        cursor = conn.cursor()

        # 1. Get Field and Planting Info
        cursor.execute("SELECT Crop, PlantingDate FROM Fields WHERE FieldId = ?", (field_id,))
        field = cursor.fetchone()
        if not field:
            return f"Field ID {field_id} not found."
        
        crop, planting_date = field
        if not planting_date:
            return f"No planting date recorded for {crop} (Field {field_id})."

        # 2. Get Growth Data
        cursor.execute("SELECT GrowthDays, HarvestDays FROM CropGrowth WHERE LOWER(CropName) = LOWER(?)", (crop,))
        growth = cursor.fetchone()
        
        if not growth:
            # Default to 90 days if unknown
            growth_days, harvest_days = 60, 90
        else:
            growth_days, harvest_days = growth

        expected_harvest = planting_date + timedelta(days=harvest_days)
        days_remaining = (expected_harvest - datetime.now()).days

        status = "Growing"
        if days_remaining <= 0:
            status = "Ready for Harvest"
        elif days_remaining <= 7:
            status = "Approaching Harvest"

        return {
            "field_id": field_id,
            "crop": crop,
            "planting_date": planting_date.strftime("%Y-%m-%d"),
            "expected_harvest_date": expected_harvest.strftime("%Y-%m-%d"),
            "days_remaining": max(0, days_remaining),
            "status": status
        }

    except Exception as e:
        return f"Error predicting harvest: {e}"
    finally:
        conn.close()
