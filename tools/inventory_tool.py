from database.db_connection import get_connection

def check_fertilizer_stock():
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT FertilizerName, StockKg FROM FertilizerInventory"
    cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Fertilizer inventory is empty."

    report = "Fertilizer Inventory Report:\n"
    for row in rows:
        report += f"- {row.FertilizerName}: {row.StockKg}kg\n"
    
    return report

def add_fertilizer(name, stock_kg):
    conn = get_connection()
    cursor = conn.cursor()

    query = "INSERT INTO FertilizerInventory (FertilizerName, StockKg) VALUES (?, ?)"
    cursor.execute(query, (name, stock_kg))
    
    conn.commit()
    conn.close()
    return f"Successfully added {name} to inventory."

def update_fertilizer_stock(name, stock_kg):
    conn = get_connection()
    cursor = conn.cursor()

    query = "UPDATE FertilizerInventory SET StockKg = ? WHERE UPPER(FertilizerName) = UPPER(?)"
    cursor.execute(query, (stock_kg, name))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return f"Successfully updated stock for {name} to {stock_kg}kg."
    else:
        return f"Error: Fertilizer '{name}' not found in inventory."

def delete_fertilizer(name):
    conn = get_connection()
    cursor = conn.cursor()

    query = "DELETE FROM FertilizerInventory WHERE UPPER(FertilizerName) = UPPER(?)"
    cursor.execute(query, (name,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return f"Successfully removed {name} from inventory."
    else:
        return f"Error: Fertilizer '{name}' not found in inventory."
