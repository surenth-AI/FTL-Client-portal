import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATHS = [
    r"d:\Fioravanti AS\axeglobal.db",
    r"d:\Fioravanti AS\track and trace\axeglobal.db",
    r"d:\FTL-DEV\axeglobal.db"
]

def main():
    for DB_PATH in DB_PATHS:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # 1. Create or get Company
            cursor.execute("SELECT id FROM company WHERE name = 'Axe Tenant'")
            company_row = cursor.fetchone()
            if company_row:
                company_id = company_row[0]
            else:
                cursor.execute('''
                    INSERT INTO company (name, address, city, country, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ("Axe Tenant", "123 Axe St", "Axe City", "Axe Country", "active", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
                company_id = cursor.lastrowid

            # 2. Create or get Admin User
            admin_email = "admin@axe.com"
            admin_password = "admin_password_123"
            password_hash = generate_password_hash(admin_password)

            cursor.execute("SELECT id FROM user WHERE email = ?", (admin_email,))
            user_row = cursor.fetchone()
            if user_row:
                cursor.execute("UPDATE user SET password_hash = ? WHERE email = ?", (password_hash, admin_email))
            else:
                cursor.execute('''
                    INSERT INTO user (name, email, password_hash, role, status, email_verified, company_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ("Axe Admin", admin_email, password_hash, "admin", "activated", 1, company_id))

            # 3. Create Sample Rates
            cursor.execute("SELECT COUNT(*) FROM rate")
            rate_count = cursor.fetchone()[0]
            if rate_count < 10:
                now = datetime.now()
                end_date = now + timedelta(days=30)
                start_str = now.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                rates = [
                    ("Shanghai", "Rotterdam", "Axe NVOCC", 1500, 150, 30, start_str, end_str, "LCL"),
                    ("Ningbo", "Hamburg", "Axe NVOCC", 1400, 100, 28, start_str, end_str, "LCL"),
                    ("Shenzhen", "Los Angeles", "Axe NVOCC", 2000, 250, 18, start_str, end_str, "FCL"),
                ]
                cursor.executemany('''
                    INSERT INTO rate (origin, destination, nvocc_name, base_rate, surcharges, transit_days, validity_start, validity_end, service_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rates)

            conn.commit()
            conn.close()
            print(f"Successfully updated {DB_PATH}")
        except Exception as e:
            print(f"Failed to update {DB_PATH}: {e}")

if __name__ == "__main__":
    main()
