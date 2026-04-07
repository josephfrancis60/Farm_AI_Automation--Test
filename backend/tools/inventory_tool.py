from database.db_connection import get_connection

def check_fertilizer_stock():
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT FertilizerName, StockKg FROM FertilizerInventory"
    cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "The fertilizer inventory is currently empty."

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
    return f"I've added {name} to the inventory for you."

def update_fertilizer_stock(name, stock_kg):
    conn = get_connection()
    cursor = conn.cursor()

    query = "UPDATE FertilizerInventory SET StockKg = ? WHERE UPPER(FertilizerName) = UPPER(?)"
    cursor.execute(query, (stock_kg, name))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return f"I've updated the stock for {name} to {stock_kg}kg."
    else:
        return f"I couldn't find {name} in the inventory to update."

def delete_fertilizer(name):
    conn = get_connection()
    cursor = conn.cursor()

    query = "DELETE FROM FertilizerInventory WHERE UPPER(FertilizerName) = UPPER(?)"
    cursor.execute(query, (name,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if affected > 0:
        return f"I've removed {name} from the inventory."
    else:
        return f"I couldn't find {name} in the inventory."
