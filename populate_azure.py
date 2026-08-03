import os
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# Load env
load_dotenv(r"d:\FTL-DEV\.env")

conn_strings = []

azure_conn_str = os.environ.get('AZURE_SQL_CONNECTION_STRING')
if azure_conn_str:
    if azure_conn_str.startswith('"') and azure_conn_str.endswith('"'):
        azure_conn_str = azure_conn_str[1:-1]
    conn_strings.append(azure_conn_str)


def populate_db(conn_str):
    print(f"\n--- Connecting to: {conn_str.split('@')[1] if '@' in conn_str else conn_str} ---")
    engine = create_engine(conn_str)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Company
        result = session.execute(text("SELECT id FROM company WHERE name = 'Axe Tenant'"))
        company_row = result.fetchone()
        if company_row:
            company_id = company_row[0]
            print(f"Company 'Axe Tenant' exists with id {company_id}")
        else:
            random_code = f"AXE-{uuid.uuid4().hex[:6].upper()}"
            random_vat = f"VAT-{uuid.uuid4().hex[:6].upper()}"
            session.execute(text("""
                INSERT INTO company (name, address, city, country, status, created_at, ftl_code, vat_number)
                OUTPUT INSERTED.id
                VALUES ('Axe Tenant', '123 Axe St', 'Axe City', 'Axe Country', 'active', GETDATE(), :code, :vat)
            """), {"code": random_code, "vat": random_vat})
            company_row = session.execute(text("SELECT id FROM company WHERE name = 'Axe Tenant'")).fetchone()
            company_id = company_row[0]
            print(f"Created company 'Axe Tenant' with id {company_id}")
            session.commit()

        # 2. User
        admin_email = "admin@axe.com"
        admin_password = "admin_password_123"
        password_hash = generate_password_hash(admin_password)

        user_row = session.execute(text("SELECT id FROM [user] WHERE email = :email"), {"email": admin_email}).fetchone()
        if user_row:
            session.execute(text("UPDATE [user] SET password_hash = :ph, status = 'activated', role = 'admin', company_id = :cid WHERE email = :email"), 
                            {"ph": password_hash, "email": admin_email, "cid": company_id})
            print(f"Updated user {admin_email}")
        else:
            session.execute(text("""
                INSERT INTO [user] (name, email, password_hash, role, status, email_verified, company_id)
                VALUES ('Axe Admin', :email, :ph, 'admin', 'activated', 1, :cid)
            """), {"email": admin_email, "ph": password_hash, "cid": company_id})
            print(f"Created admin user: {admin_email}")
        session.commit()

        # 3. Rates
        rate_count = session.execute(text("SELECT COUNT(*) FROM rate")).fetchone()[0]
        if rate_count < 10:
            now = datetime.now()
            end_date = now + timedelta(days=30)
            start_str = now.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            rates = [
                {"o": "Shanghai", "d": "Rotterdam", "n": "Axe NVOCC", "b": 1500, "s": 150, "t": 30, "vs": start_str, "ve": end_str, "st": "LCL"},
                {"o": "Ningbo", "d": "Hamburg", "n": "Axe NVOCC", "b": 1400, "s": 100, "t": 28, "vs": start_str, "ve": end_str, "st": "LCL"},
                {"o": "Shenzhen", "d": "Los Angeles", "n": "Axe NVOCC", "b": 2000, "s": 250, "t": 18, "vs": start_str, "ve": end_str, "st": "FCL"},
            ]
            
            for r in rates:
                session.execute(text("""
                    INSERT INTO rate (origin, destination, nvocc_name, base_rate, surcharges, transit_days, validity_start, validity_end, service_type)
                    VALUES (:o, :d, :n, :b, :s, :t, :vs, :ve, :st)
                """), r)
            session.commit()
            print("Populated sample rates")
        else:
            print("Rates already exist, skipping sample rate creation")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

def main():
    for c in conn_strings:
        populate_db(c)

if __name__ == "__main__":
    main()
