from database.db_connection import get_connection

def get_fertilizer_recommendation(crop_name):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT Crop, SoilType, Area FROM Fields WHERE UPPER(Crop) = UPPER(?)"
    cursor.execute(query, (crop_name,))

    row = cursor.fetchone()
    conn.close()

    if row:
        crop, soil, area = row
        return {
            "crop": crop,
            "soil_type": soil,
            "area_acres": area,
            "message": f"Retrieved data for {crop}. Soil type: {soil}, Area: {area} acres. Please recommend a suitable fertilizer."
        }
    else:
        return {"error": f"No data found for crop: {crop_name}."}