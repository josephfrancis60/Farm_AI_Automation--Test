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
        recommendation = ""
        if soil.lower() == 'loamy':
            recommendation = "a balanced N-P-K fertilizer is recommended."
        elif soil.lower() == 'sandy':
            recommendation = "a nitrogen-rich fertilizer is recommended due to fast drainage."
        elif soil.lower() == 'clay':
            recommendation = "a slow-release nutrient mix is recommended for better absorption."
        else:
            recommendation = "a standard organic fertilizer is recommended."
            
        return f"Based on {soil} soil and {area} acre area, {recommendation}"
    else:
        return f"No data found for crop: {crop_name}."