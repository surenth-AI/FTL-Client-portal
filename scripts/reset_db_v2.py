import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.models import User, Company, Rate
from werkzeug.security import generate_password_hash

from sqlalchemy import text

def reset_db():
    app = create_app()
    with app.app_context():
        print("Dropping all tables (ignoring foreign keys)...")
        db.session.execute(text('PRAGMA foreign_keys = OFF;'))
        db.drop_all()
        db.session.execute(text('PRAGMA foreign_keys = ON;'))
        print("Creating all tables...")
        db.create_all()

        
        # 1. Seed Multi-Role Staff
        super_admin = User(
            name='Super User',
            email='super@ftl.com',
            password_hash=generate_password_hash('admin123'),
            role='super_admin',
            status='active'
        )
        db.session.add(super_admin)

        admin = User(
            name='System Admin',
            email='admin@ftl.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            status='active'
        )
        db.session.add(admin)

        finance_exec = User(
            name='Finance Lead',
            email='finance@ftl.com',
            password_hash=generate_password_hash('finance123'),
            role='operation_executive',
            department='finance',
            status='active'
        )
        db.session.add(finance_exec)

        ops_exec = User(
            name='Export Manager',
            email='export@ftl.com',
            password_hash=generate_password_hash('export123'),
            role='operation_executive',
            department='export',
            status='active'
        )
        db.session.add(ops_exec)

        
        # 2. Seed a Sample Active Company
        demo_company = Company(
            ftl_code='FTL-BE-001',
            name='Global Logistics SA',
            address='Rue de la Loi 200',
            zip_code='1000',
            city='Brussels',
            country='Belgium',
            vat_number='BE0123456789',
            eori_number='BE0123456789EORI',
            status='active'
        )
        db.session.add(demo_company)
        db.session.flush()
        
        # 3. Seed an active user for the sample company
        company_user = User(
            name='John Doe',
            email='john@global-logistics.com',
            password_hash=generate_password_hash('customer123'),
            role='customer',
            mobile='+32 456 78 90 12',
            company_id=demo_company.id,
            status='active'
        )
        db.session.add(company_user)
        
        # 4. Seed a pending company (for testing approval flow)
        pending_company = Company(
            name='New Tech Forwarding',
            address='Main St 5',
            zip_code='2000',
            city='Antwerp',
            country='Belgium',
            vat_number='BE9876543210',
            eori_number='BE9876543210EORI',
            status='pending_finance'
        )
        db.session.add(pending_company)
        db.session.flush()
        
        pending_user = User(
            name='Jane Smith',
            email='jane@newtech.com',
            password_hash=generate_password_hash('password123'),
            role='customer',
            mobile='+32 111 22 33 44',
            company_id=pending_company.id,
            status='pending_ops'
        )
        db.session.add(pending_user)

        db.session.commit()
        print("Database reset and seeded successfully!")
        print("Admin: admin@ftl.com / admin123")
        print("Customer: john@global-logistics.com / customer123 (FTL Code: FTL-BE-001)")

if __name__ == '__main__':
    reset_db()
