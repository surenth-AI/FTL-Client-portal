import sqlite3
import os
import glob
from werkzeug.security import generate_password_hash

db_path = 'd:/FTL-DEV/axeglobal.db'
if not os.path.exists(db_path):
    print('DB not found at default instance path. Searching...')
    print(glob.glob('d:/FTL-DEV/**/*.db', recursive=True))
else:
    print('DB found at:', db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, email, role, password_hash FROM user WHERE email='admin@axeglobal.com'")
    user = c.fetchone()
    print('Admin in DB:', user)
    
    if not user:
        print("Admin user does not exist! Creating it now...")
        pwd_hash = generate_password_hash('Admin@123456!')
        c.execute("INSERT INTO user (name, email, password_hash, role, company_name) VALUES (?, ?, ?, ?, ?)", 
                  ('System Admin', 'admin@axeglobal.com', pwd_hash, 'super_admin', 'AxeGlobal'))
        conn.commit()
        print("Created admin user!")
    else:
        print("Admin user exists. Resetting password just in case...")
        pwd_hash = generate_password_hash('Admin@123456!')
        c.execute("UPDATE user SET password_hash = ? WHERE email = 'admin@axeglobal.com'", (pwd_hash,))
        conn.commit()
        print("Password reset for admin user.")

    c.execute('SELECT email, role FROM user')
    all_users = c.fetchall()
    print('All users in DB:', all_users)
