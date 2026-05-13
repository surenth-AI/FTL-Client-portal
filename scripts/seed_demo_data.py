import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Ensure parent path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.models import User, Company, Booking, TrackingEvent, Rate

app = create_app()

def seed_demo():
    with app.app_context():
        print("Starting data population...")
        
        # 1. Create a Demo Company
        comp = Company.query.filter_by(vat_number='US987654321').first()
        if not comp:
            comp = Company(
                ftl_code='FTL-US-101',
                name='Universal Forwarding Inc',
                address='500 5th Ave',
                zip_code='10110',
                city='New York',
                country='USA',
                vat_number='US987654321',
                status='active'
            )
            db.session.add(comp)
            db.session.commit()
            print("SUCCESS: Company created: Universal Forwarding Inc")
        else:
            print("INFO: Company already exists.")

        # 2. Create Customer User
        cust = User.query.filter_by(email='customer@axeglobal.com').first()
        if not cust:
            cust = User(
                name='John Doe',
                email='customer@axeglobal.com',
                password_hash=generate_password_hash('customer123'),
                role='customer',
                status='active',
                company_id=comp.id
            )
            db.session.add(cust)
            db.session.commit()
            print("SUCCESS: Customer created: customer@axeglobal.com / customer123")
        else:
            print("INFO: Customer already exists.")

        # 3. Create an Agent User
        agent = User.query.filter_by(email='agent@axeglobal.com').first()
        if not agent:
            agent = User(
                name='Sarah Jenkins',
                email='agent@axeglobal.com',
                password_hash=generate_password_hash('agent123'),
                role='agent',
                status='active'
            )
            db.session.add(agent)
            db.session.commit()
            print("SUCCESS: Agent created: agent@axeglobal.com / agent123")
        else:
            print("INFO: Agent already exists.")

        # 4. Create Sample Bookings
        if Booking.query.filter_by(user_id=cust.id).count() == 0:
            b1 = Booking(
                user_id=cust.id,
                origin='Shanghai (CNSHA)',
                destination='Hamburg (DEHAM)',
                volume=5.5,
                selected_nvocc='Maersk Line',
                total_cost=1250.0,
                service_type='LCL',
                status='In Transit',
                mbl_number='MAEU4928109283',
                hbl_number='AXGSHA250981',
                vessel_name='Maersk Mc-Kinney Moller',
                voyage_number='2502W',
                eta_pod=datetime.utcnow() + timedelta(days=15),
                etd=datetime.utcnow() - timedelta(days=10),
                payment_status='CONFIRMED'
            )
            
            b2 = Booking(
                user_id=cust.id,
                origin='Antwerp (BEANR)',
                destination='New York (USNYC)',
                volume=12.0,
                selected_nvocc='Hapag-Lloyd',
                total_cost=3200.0,
                service_type='LCL',
                status='Booked',
                mbl_number='HLCUANT29038',
                hbl_number='AXGANR251103',
                vessel_name='Hamburg Express',
                voyage_number='89W',
                eta_pod=datetime.utcnow() + timedelta(days=20),
                etd=datetime.utcnow() + timedelta(days=5),
                payment_status='UNPAID'
            )

            db.session.add_all([b1, b2])
            db.session.commit()
            
            # Add Tracking Events for Booking 1
            e1 = TrackingEvent(booking_id=b1.id, status='Gate-in at Terminal', location='Shanghai CNSHA', timestamp=datetime.utcnow() - timedelta(days=12))
            e2 = TrackingEvent(booking_id=b1.id, status='Vessel Departed', location='Shanghai CNSHA', timestamp=datetime.utcnow() - timedelta(days=10))
            e3 = TrackingEvent(booking_id=b1.id, status='In Transit Ocean', location='East China Sea', timestamp=datetime.utcnow() - timedelta(days=5))
            
            db.session.add_all([e1, e2, e3])
            db.session.commit()
            print("SUCCESS: Demo Bookings and Tracking Events added for Customer!")
        else:
            print("INFO: Demo Bookings already exist.")

        # 5. Seed Rate Sheet if empty
        if Rate.query.count() == 0:
            r1 = Rate(
                origin='Shanghai (CNSHA)', destination='Hamburg (DEHAM)',
                nvocc_name='Cosco Shipping', carrier_name='COSCO', base_rate=110.0, surcharges=150.0,
                transit_days=28, validity_start=datetime.utcnow().date(), validity_end=(datetime.utcnow() + timedelta(days=60)).date(),
                service_type='LCL'
            )
            r2 = Rate(
                origin='Shanghai (CNSHA)', destination='Hamburg (DEHAM)',
                nvocc_name='OOCL Logistics', carrier_name='OOCL', base_rate=135.0, surcharges=120.0,
                transit_days=24, validity_start=datetime.utcnow().date(), validity_end=(datetime.utcnow() + timedelta(days=60)).date(),
                service_type='LCL'
            )
            db.session.add_all([r1, r2])
            db.session.commit()
            print("SUCCESS: Market Rates populated!")
        else:
            print("INFO: Rates already seeded.")

        print("\nCOMPLETED: All demo users and logistics datasets populated successfully!")

if __name__ == "__main__":
    seed_demo()
