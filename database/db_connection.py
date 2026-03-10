import pyodbc

def get_connection():

    # Db connection string
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=(localdb)\\MSSQLLocalDB;" 
        "DATABASE=FarmAI;"
        "Trusted_Connection=yes;"
    )

    return conn