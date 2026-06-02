"""
Creates the 'registration' table directly on the Azure SQL Server
using raw pyodbc connection (bypasses SQLAlchemy's create_all limitation).
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

server = os.environ.get('DB_SERVER')
database = os.environ.get('DB_NAME')
username = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
driver = os.environ.get('DB_DRIVER', '{SQL Server}')

conn_str = (
    f"Driver={driver};"
    f"Server={server},1433;"
    f"Database={database};"
    f"Uid={username};"
    f"Pwd={password};"
)

print(f"Connecting to {server}/{database}...")
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Check if table already exists
cursor.execute("""
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = 'registration'
""")
exists = cursor.fetchone()[0]

if exists:
    print("Table 'registration' already exists. Checking for missing columns...")
    alterations = [
        ("reject_reason", "ALTER TABLE registration ADD reject_reason NVARCHAR(500) NULL"),
        ("info_message",  "ALTER TABLE registration ADD info_message NVARCHAR(MAX) NULL"),
        ("city",          "ALTER TABLE registration ADD city NVARCHAR(100) NULL"),
    ]
    for col_name, sql in alterations:
        cursor.execute(f"""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME='registration' AND COLUMN_NAME='{col_name}'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute(sql)
            print(f"  Added missing column: {col_name}")
        else:
            print(f"  Column '{col_name}' OK")
else:
    print("Creating table 'registration'...")
    cursor.execute("""
        CREATE TABLE registration (
            id               INT IDENTITY(1,1) PRIMARY KEY,
            registration_id  NVARCHAR(36)   NOT NULL UNIQUE,
            email            NVARCHAR(120)  NOT NULL,
            full_name        NVARCHAR(120)  NOT NULL,
            phone            NVARCHAR(30)   NULL,
            company_name     NVARCHAR(200)  NOT NULL,
            city             NVARCHAR(100)  NULL,
            country_code     NVARCHAR(5)    NOT NULL,
            vat              NVARCHAR(50)   NULL,
            created_on       DATETIME2      NOT NULL DEFAULT GETUTCDATE(),
            status           NVARCHAR(20)   NOT NULL DEFAULT 'pending',
            reject_reason    NVARCHAR(500)  NULL,
            info_message     NVARCHAR(MAX)  NULL
        )
    """)
    print("Table 'registration' created successfully!")

conn.commit()
cursor.close()
conn.close()
print("Done.")
