import sqlite3
import os

db_path = 'axeglobal.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS arrival_notice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                recipient_type VARCHAR(50) NOT NULL,
                recipient_email VARCHAR(120) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                sent_at DATETIME,
                opened_at DATETIME,
                pdf_path VARCHAR(255),
                FOREIGN KEY(booking_id) REFERENCES booking(id)
            )
        """)
        conn.commit()
        conn.close()
        print("Successfully created arrival_notice table.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database {db_path} not found.")
