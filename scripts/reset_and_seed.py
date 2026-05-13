import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.models import User, Booking, Rate, ProformaInvoice, Invoice, TrackingEvent, EdiPreAlert, AuditLog

def clean_db():
    print("Cleaning database and uploads...")
    db.drop_all()
    db.create_all()
    
    # Clear uploads folder
    upload_path = 'uploads'
    if os.path.exists(upload_path):
        for root, dirs, files in os.walk(upload_path):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except:
                    pass
    print("Database and uploads cleaned.")

def seed_users():
    print("Seeding users...")
    users = [
        # Admins
        ('Admin One', 'admin1@axeglobal.com', 'admin123', 'admin'),
        ('Admin Two', 'admin2@axeglobal.com', 'admin123', 'admin'),
        # Customers
        ('Global Trading Ltd', 'customer1@axeglobal.com', 'cust123', 'customer'),
        ('Nordic Imports Oy', 'customer2@axeglobal.com', 'cust123', 'customer'),
        # Agents
        ('Hamburg Port Agent', 'agent1@axeglobal.com', 'agent123', 'agent'),
        ('Rotterdam Logistics', 'agent2@axeglobal.com', 'agent123', 'agent'),
    ]
    
    for name, email, password, role in users:
        u = User(name=name, email=email, password_hash=generate_password_hash(password), role=role)
        db.session.add(u)
    db.session.commit()
    print("Users seeded.")

def seed_logistics_data():
    print("Seeding logistics data...")
    cust1 = User.query.filter_by(email='customer1@axeglobal.com').first()
    cust2 = User.query.filter_by(email='customer2@axeglobal.com').first()
    
    # 1. Bookings
    b1 = Booking(
        user_id=cust1.id,
        origin='Shanghai, China',
        destination='Hamburg, Germany',
        status='In Transit',
        vessel_name='MAERSK SEOUL',
        voyage_number='241W',
        mbl_number='SHAGHAM456123',
        volume=24.5,
        selected_nvocc='Maersk Line',
        total_cost=2180.0
    )
    
    b2 = Booking(
        user_id=cust2.id,
        origin='Jebel Ali, UAE',
        destination='Rotterdam, Netherlands',
        status='Booked',
        vessel_name='CMA CGM ANTOINE',
        voyage_number='FE42',
        mbl_number='DXBRTM789000',
        volume=12.2,
        selected_nvocc='CMA CGM',
        total_cost=1250.0
    )
    
    db.session.add_all([b1, b2])
    db.session.commit()

    # 2. Financial Documents for Booking 1
    p1 = ProformaInvoice(
        booking_id=b1.id,
        charge_lines=[
            {'description': 'Ocean Freight (Lumpsum)', 'amount': 1850.0},
            {'description': 'Destination Handling (THC)', 'amount': 245.0},
            {'description': 'Customs Clearance Fee', 'amount': 85.0}
        ],
        subtotal=2180.0,
        taxes=0.0,
        total_amount=2180.0,
        currency='USD',
        payment_status='CONFIRMED',
        payment_reference='SWIFT-SH-99218',
        payment_confirmed_at=datetime.utcnow() - timedelta(days=1)
    )
    db.session.add(p1)
    db.session.commit()
    
    # Create Final Invoice for the confirmed payment
    inv1 = Invoice(
        proforma_id=p1.id,
        booking_id=b1.id,
        invoice_number='AXEGLOBAL/2026/0001',
        charge_lines=p1.charge_lines,
        total_amount=p1.total_amount,
        currency=p1.currency,
        issued_at=datetime.utcnow() - timedelta(days=1)
    )
    db.session.add(inv1)
    
    # 3. Pending Proforma for Booking 2
    p2 = ProformaInvoice(
        booking_id=b2.id,
        charge_lines=[
            {'description': 'Ocean Freight', 'amount': 1200.0},
            {'description': 'Admin Fee', 'amount': 50.0}
        ],
        subtotal=1250.0,
        taxes=0.0,
        total_amount=1250.0,
        currency='EUR',
        payment_status='UNPAID'
    )
    db.session.add(p2)
    
    # 4. Tracking Events
    e1 = TrackingEvent(booking_id=b1.id, status='In Transit', location='Suez Canal', timestamp=datetime.utcnow() - timedelta(days=3))
    e2 = TrackingEvent(booking_id=b1.id, status='Departed POL', location='Shanghai Port', timestamp=datetime.utcnow() - timedelta(days=10))
    db.session.add_all([e1, e2])

    # 5. Audit Logs
    audit = AuditLog(
        user_id=1,
        action='RELEASE_CARGO',
        target_type='Booking',
        target_id=b1.id,
        details='Payment confirmed via SWIFT-SH-99218. Final Invoice AXEGLOBAL/2026/0001 generated.'
    )
    db.session.add(audit)
    
    db.session.commit()
    print("Logistics data seeded.")

def create_sample_files():
    print("Creating sample data files for upload...")
    # 1. Rates CSV
    rates_csv = """origin,destination,nvocc_name,base_rate,surcharges,transit_days,validity_start,validity_end
Shanghai,Hamburg,Maersk Line,1200,450,32,2026-01-01,2026-12-31
Ningbo,Rotterdam,MSC,1150,400,34,2026-01-01,2026-12-31
Jebel Ali,Antwerp,Hapag-Lloyd,900,300,22,2026-01-01,2026-12-31
Singapore,Felixstowe,CMA CGM,1050,350,28,2026-01-01,2026-12-31
"""
    with open('sample_data/rates.csv', 'w') as f:
        f.write(rates_csv)
    
    # 2. EDI Pre-alert Sample
    edi_sample = """SHIPMENT PRE-ALERT
------------------
MBL: MSKU99228833
HBL: HBL-776611
VESSEL: MAERSK MC-KINNEY MOLLER
VOYAGE: 402E
POL: SHANGHAI
POD: HAMBURG
CONSIGNEE: GLOBAL TRADING LTD
NOTIFY: HAMBURG PORT AGENT
CARGO: 1 x 40HC STC ELECTRONIC COMPONENTS
WEIGHT: 18500 KGS
VOLUME: 68 CBM
"""
    with open('sample_data/arrival_prealert.txt', 'w') as f:
        f.write(edi_sample)
    
    print("Sample files created in /sample_data/")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        clean_db()
        seed_users()
        seed_logistics_data()
        create_sample_files()
    print("\nSUCCESS: Application is clean and seeded for demo!")
    print("Users created (Password: admin123 for admins, cust123 for customers, agent123 for agents):")
    print("- admin1@axeglobal.com, admin2@axeglobal.com")
    print("- customer1@axeglobal.com, customer2@axeglobal.com")
    print("- agent1@axeglobal.com, agent2@axeglobal.com")
