from database.db_connection import get_connection

def check_schema():
    conn = get_connection()
    cursor = conn.cursor()
    tables = ['Fields', 'FertilizerInventory', 'IrrigationHistory']
    for table in tables:
        print(f"--- Schema for {table} ---")
        cursor.execute(f"SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
        for row in cursor.fetchall():
            print(row)
    conn.close()

if __name__ == "__main__":
    check_schema()
