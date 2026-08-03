import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load env
load_dotenv(r"d:\FTL-DEV\.env")

azure_conn_str = os.environ.get('AZURE_SQL_CONNECTION_STRING')
if azure_conn_str:
    if azure_conn_str.startswith('"') and azure_conn_str.endswith('"'):
        azure_conn_str = azure_conn_str[1:-1]

print(f"Connecting to: {azure_conn_str.split('@')[1] if '@' in azure_conn_str else azure_conn_str}")

engine = create_engine(azure_conn_str)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Get Axe Tenant
    result = session.execute(text("SELECT id FROM company WHERE name = 'Axe Tenant'"))
    company_row = result.fetchone()
    if not company_row:
        print("Axe Tenant not found!")
        exit(1)
    company_id = company_row[0]

    email = "sample@axeglobal.com"
    new_password = "sample_password_123"
    password_hash = generate_password_hash(new_password)

    user_row = session.execute(text("SELECT id FROM [user] WHERE email = :email"), {"email": email}).fetchone()
    
    if user_row:
        session.execute(text("""
            UPDATE [user] 
            SET password_hash = :ph, status = 'activated', company_id = :cid 
            WHERE email = :email
        """), {"ph": password_hash, "cid": company_id, "email": email})
        print(f"User {email} found. Password reset and assigned to Axe Tenant.")
    else:
        session.execute(text("""
            INSERT INTO [user] (name, email, password_hash, role, status, email_verified, company_id)
            VALUES ('Sample User', :email, :ph, 'customer', 'activated', 1, :cid)
        """), {"email": email, "ph": password_hash, "cid": company_id})
        print(f"User {email} created in Axe Tenant.")
    
    session.commit()
    print("---")
    print("Credentials for sample@axeglobal.com:")
    print(f"Password: {new_password}")

except Exception as e:
    session.rollback()
    print(f"Error: {e}")
finally:
    session.close()
