from database.db_connection import get_connection

def check_field_identity():
    conn = get_connection()
    cursor = conn.cursor()
    print("--- Detailed Schema for Fields ---")
    # Check if FieldId is an identity column
    query = """
    SELECT COLUMN_NAME, 
           COLUMNPROPERTY(OBJECT_ID(TABLE_SCHEMA + '.' + TABLE_NAME), COLUMN_NAME, 'IsIdentity') AS IsIdentity
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Fields' AND COLUMN_NAME = 'FieldId'
    """
    cursor.execute(query)
    row = cursor.fetchone()
    if row:
        print(f"Column: {row[0]}, IsIdentity: {row[1]}")
    else:
        print("Column FieldId not found.")
    
    # Also check current data
    cursor.execute("SELECT * FROM Fields")
    rows = cursor.fetchall()
    print("\n--- Current Data in Fields ---")
    for r in rows:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    check_field_identity()
