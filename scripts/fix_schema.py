import sqlite3
import os

db_path = 'axeglobal.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE user ADD COLUMN gmail_token TEXT")
        conn.commit()
        conn.close()
        print("Successfully added gmail_token column to user table.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database {db_path} not found.")
