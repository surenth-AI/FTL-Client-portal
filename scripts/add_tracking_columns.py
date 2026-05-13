import sqlite3
import os

db_path = 'axeglobal.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add missing columns to booking table
        columns = [
            ('mbl_number', 'VARCHAR(100)'),
            ('hbl_number', 'VARCHAR(100)'),
            ('vessel_name', 'VARCHAR(100)'),
            ('voyage_number', 'VARCHAR(50)'),
            ('eta_pod', 'DATETIME')
        ]
        
        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE booking ADD COLUMN {col_name} {col_type}")
                print(f"Added {col_name} to booking table.")
            except sqlite3.OperationalError:
                print(f"Column {col_name} already exists.")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database {db_path} not found.")
