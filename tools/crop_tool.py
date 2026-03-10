from database.db_connection import get_connection

def get_all_crops():
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT FieldId, Crop, SoilType, Area FROM Fields"
    cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No crops found in the fields."

    summary = "Current crops in the farm:\n"
    for row in rows:
        summary += f"- ID: {row.FieldId} | {row.Crop} ({row.SoilType} soil, {row.Area} acres)\n"
    
    return summary

def get_crop_names():
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT Crop FROM Fields"
    cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    crops = [row.Crop.lower() for row in rows]

    return crops

def add_crop(crop, soil_type, area):
    conn = get_connection()
    cursor = conn.cursor()

    # Get the next FieldId if it's not an identity column
    cursor.execute("SELECT ISNULL(MAX(FieldId), 0) + 1 FROM Fields")
    next_id = cursor.fetchone()[0]

    query = "INSERT INTO Fields (FieldId, Crop, SoilType, Area) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (next_id, crop, soil_type, area))
    
    conn.commit()
    conn.close()
    return f"Successfully added {crop} (ID: {next_id}) to the fields."

def update_field(field_id, crop=None, soil_type=None, area=None):
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []
    if crop:
        updates.append("Crop = ?")
        params.append(crop)
    if soil_type:
        updates.append("SoilType = ?")
        params.append(soil_type)
    if area:
        updates.append("Area = ?")
        params.append(area)

    if not updates:
        return "No updates provided."

    params.append(field_id)
    query = f"UPDATE Fields SET {', '.join(updates)} WHERE FieldId = ?"
    cursor.execute(query, tuple(params))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return f"Successfully updated field {field_id}."
    else:
        return f"Error: Field ID {field_id} not found."

def delete_field(field_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = "DELETE FROM Fields WHERE FieldId = ?"
    cursor.execute(query, (field_id,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return f"Successfully deleted field {field_id}."
    else:
        return f"Error: Field ID {field_id} not found."

def get_field_id_by_crop(crop_name):
    """
    Get the FieldId for a given crop name.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Use case-insensitive matching
    query = "SELECT FieldId FROM Fields WHERE LOWER(Crop) = LOWER(?)"
    cursor.execute(query, (crop_name,))
    
    row = cursor.fetchone()
    conn.close()

    if row:
        return row.FieldId
    return None
