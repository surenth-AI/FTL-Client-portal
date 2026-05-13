import os
import sys
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.models import User, Booking, ProformaInvoice, Invoice, TrackingEvent

def seed_billing_data():
    print("Seeding bulk billing data...")
    
    customers = User.query.filter_by(role='customer').all()
    if not customers:
        print("No customers found. Please run reset_and_seed.py first.")
        return

    ports = ["Shanghai", "Ningbo", "Rotterdam", "Hamburg", "New York", "Jebel Ali", "Antwerp"]
    vessels = ["MAERSK MC-KINNEY MOLLER", "MSC GULSUN", "CMA CGM JACQUES SAADE", "COSCO UNIVERSE"]
    
    # Generate 15 Pending Proformas (UNPAID)
    for i in range(15):
        cust = random.choice(customers)
        # Create a Booking
        b = Booking(
            user_id=cust.id,
            origin=random.choice(ports[:3]),
            destination=random.choice(ports[3:]),
            status='In Transit',
            vessel_name=random.choice(vessels),
            voyage_number=f"{random.randint(100, 999)}W",
            mbl_number=f"MBL{random.randint(1000000, 9999999)}",
            volume=random.uniform(5, 50),
            selected_nvocc=random.choice(['Maersk', 'MSC', 'CMA CGM']),
            total_cost=random.uniform(800, 4500)
        )
        db.session.add(b)
        db.session.flush() # Get booking ID
        
        freight = random.uniform(1000, 3000)
        thc = random.uniform(200, 400)
        total = freight + thc
        
        p = ProformaInvoice(
            booking_id=b.id,
            charge_lines=[
                {'description': 'Ocean Freight (Lumpsum)', 'amount': round(freight, 2)},
                {'description': 'Destination Handling (THC)', 'amount': round(thc, 2)}
            ],
            subtotal=round(total, 2),
            taxes=0.0,
            total_amount=round(total, 2),
            currency=random.choice(['USD', 'EUR']),
            payment_status='UNPAID',
            issued_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
        )
        db.session.add(p)

    # Generate 20 Paid Invoices (CONFIRMED)
    for i in range(20):
        cust = random.choice(customers)
        b = Booking(
            user_id=cust.id,
            origin=random.choice(ports[:3]),
            destination=random.choice(ports[3:]),
            status='Released',
            vessel_name=random.choice(vessels),
            voyage_number=f"{random.randint(100, 999)}E",
            mbl_number=f"MBL{random.randint(1000000, 9999999)}",
            volume=random.uniform(5, 50),
            selected_nvocc=random.choice(['Maersk', 'MSC', 'CMA CGM']),
            total_cost=random.uniform(800, 4500)
        )
        db.session.add(b)
        db.session.flush()
        
        freight = random.uniform(1000, 5000)
        thc = random.uniform(200, 400)
        total = freight + thc
        
        paid_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        issued_date = paid_date - timedelta(days=random.randint(1, 5))
        
        p = ProformaInvoice(
            booking_id=b.id,
            charge_lines=[
                {'description': 'Ocean Freight (Lumpsum)', 'amount': round(freight, 2)},
                {'description': 'Destination Handling (THC)', 'amount': round(thc, 2)}
            ],
            subtotal=round(total, 2),
            taxes=0.0,
            total_amount=round(total, 2),
            currency=random.choice(['USD', 'EUR']),
            payment_status='CONFIRMED',
            payment_reference=f"TRN-{random.randint(10000, 99999)}",
            payment_confirmed_at=paid_date,
            issued_at=issued_date
        )
        db.session.add(p)
        db.session.flush()
        
        inv_number = f"AXEGLOBAL/2026/{str(p.id).zfill(4)}"
        inv = Invoice(
            proforma_id=p.id,
            booking_id=b.id,
            invoice_number=inv_number,
            charge_lines=p.charge_lines,
            total_amount=p.total_amount,
            currency=p.currency,
            issued_at=paid_date
        )
        db.session.add(inv)

    db.session.commit()
    print("Successfully seeded bulk Billing data (15 Pending, 20 Paid).")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_billing_data()
