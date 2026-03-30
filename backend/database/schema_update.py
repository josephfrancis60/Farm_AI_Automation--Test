from database.db_connection import get_connection

def update_schema():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("Starting schema updates...")

        # 1. Update Fields table to add PlantingDate
        try:
            cursor.execute("ALTER TABLE Fields ADD PlantingDate DATETIME")
            print("- Added PlantingDate to Fields table.")
        except Exception as e:
            if "already has a column named" in str(e) or "already exists" in str(e).lower():
                print("- PlantingDate already exists in Fields table.")
            else:
                print(f"- Error adding PlantingDate: {e}")

        # 2. Create WeatherHistory table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'WeatherHistory')
        CREATE TABLE WeatherHistory (
            Id INT IDENTITY PRIMARY KEY,
            Timestamp DATETIME DEFAULT GETDATE(),
            Location NVARCHAR(100),
            Temperature FLOAT,
            Rain NVARCHAR(100),
            Humidity FLOAT
        )
        """)
        print("- WeatherHistory table ready.")

        # 3. Create SystemState table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SystemState')
        BEGIN
            CREATE TABLE SystemState (
                Id INT PRIMARY KEY,
                LastRunTime DATETIME
            )
            INSERT INTO SystemState (Id, LastRunTime) VALUES (1, GETDATE())
        END
        """)
        print("- SystemState table ready.")

        # 4. Create CropGrowth table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CropGrowth')
        CREATE TABLE CropGrowth (
            CropName NVARCHAR(100) PRIMARY KEY,
            GrowthDays INT,
            HarvestDays INT
        )
        """)
        print("- CropGrowth table ready.")
        
        # Populate CropGrowth with defaults if empty
        cursor.execute("SELECT COUNT(*) FROM CropGrowth")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO CropGrowth (CropName, GrowthDays, HarvestDays) VALUES
            ('Tomato', 60, 80),
            ('Corn', 80, 100),
            ('Sugarcane', 300, 365),
            ('Potato', 70, 90)
            """)
            print("- Populated default crop growth data.")

        conn.commit()
        print("Schema updates completed successfully.")

    except Exception as e:
        print(f"Error during schema update: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_schema()
