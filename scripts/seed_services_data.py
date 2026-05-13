import os
from app import db, create_app
from app.models.models import Job, User, VendorInvoice, VendorInvoiceItem
from datetime import datetime, timedelta
import random

def seed():
    app = create_app()
    with app.app_context():
        print("Starting deep seed for client demo...")
        # Clear existing data to avoid conflicts
        db.session.query(VendorInvoiceItem).delete()
        db.session.query(VendorInvoice).delete()
        db.session.query(Job).delete()
        
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("No admin user found. Run reset_admin.py first.")
            return

        # Seed Jobs that match our generated SOA Excel
        # JOB-2026-100 to JOB-2026-119
        for i in range(20):
            job_no = f"JOB-{2026}-{100 + i}"
            j = Job(
                job_number=job_no, 
                user_id=admin.id, 
                incoterms="FOB", 
                type="IMPORT SEA", 
                job_date=datetime.utcnow()
            )
            db.session.add(j)
            
            # Create a matching invoice for even jobs
            if i % 2 == 0:
                amount = random.uniform(1000, 3000)
                inv = VendorInvoice(
                    invoice_number=job_no, # Matching Job No as per SOA logic
                    supplier="Maersk Line" if i < 10 else "MSC Mediterranean",
                    amount=amount,
                    currency="USD",
                    match_status="MATCHED 100%",
                    user_id=admin.id,
                    invoice_date=datetime.utcnow()
                )
                db.session.add(inv)
                db.session.flush()
                
                # Add item
                item = VendorInvoiceItem(
                    invoice_id=inv.id,
                    description="Ocean Freight Service",
                    total_price=amount,
                    job_id=job_no
                )
                db.session.add(item)
        
        db.session.commit()
        print("Database seeded with 20 demo jobs and matching invoices.")

if __name__ == "__main__":
    seed()
