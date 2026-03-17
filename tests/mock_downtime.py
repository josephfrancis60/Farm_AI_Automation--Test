from database.db_connection import get_connection
from datetime import datetime, timedelta

def mock_downtime():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Set LastRunTime to 2.5 hours ago
    last_run = datetime.now() - timedelta(hours=2, minutes=30)
    print(f"Mocking LastRunTime to: {last_run}")
    
    cursor.execute("UPDATE SystemState SET LastRunTime = ? WHERE Id = 1", (last_run,))
    conn.commit()
    conn.close()
    print("SystemState updated successfully.")

if __name__ == "__main__":
    mock_downtime()
