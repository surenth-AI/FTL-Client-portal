import sys
import os

# Add the app directory to the sys.path to easily import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.models import User, Company, Rate
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

app = create_app()

def main():
    with app.app_context():
        # Create Axe Tenant Company if not exists
        company = Company.query.filter_by(name="Axe Tenant").first()
        if not company:
            company = Company(name="Axe Tenant", address="123 Axe St", city="Axe City", country="Axe Country", status="active")
            db.session.add(company)
            db.session.commit()
            print("Created company 'Axe Tenant'")

        # Create Admin User
        admin_email = "admin@axe.com"
        admin_password = "admin_password_123"
        user = User.query.filter_by(email=admin_email).first()
        if not user:
            user = User(
                name="Axe Admin",
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                role="admin",
                status="activated",
                email_verified=True,
                company_id=company.id
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created admin user: {admin_email}")
        else:
            print(f"Admin user {admin_email} already exists")

        # Create sample Rates
        if Rate.query.count() < 10:
            sample_rates = [
                Rate(origin="Shanghai", destination="Rotterdam", nvocc_name="Axe NVOCC", base_rate=1500, surcharges=150, transit_days=30, validity_start=datetime.now().date(), validity_end=(datetime.now() + timedelta(days=30)).date(), service_type="LCL"),
                Rate(origin="Ningbo", destination="Hamburg", nvocc_name="Axe NVOCC", base_rate=1400, surcharges=100, transit_days=28, validity_start=datetime.now().date(), validity_end=(datetime.now() + timedelta(days=30)).date(), service_type="LCL"),
                Rate(origin="Shenzhen", destination="Los Angeles", nvocc_name="Axe NVOCC", base_rate=2000, surcharges=250, transit_days=18, validity_start=datetime.now().date(), validity_end=(datetime.now() + timedelta(days=30)).date(), service_type="FCL"),
            ]
            db.session.add_all(sample_rates)
            db.session.commit()
            print("Populated sample rates")
        else:
            print("Rates already exist, skipping sample rate creation")

        print("---")
        print("Login Credentials:")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")

if __name__ == "__main__":
    main()
