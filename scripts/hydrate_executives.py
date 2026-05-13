import sys
sys.path.append('.')
from app import create_app, db
from app.models.models import User, Company, Booking
from werkzeug.security import generate_password_hash

def run():
    app = create_app()
    with app.app_context():
        hashed = generate_password_hash('Admin@123')
        
        # Ensure Finance Lead exists and is active
        u3 = User.query.filter_by(email='finance@ftl.com').first()
        if not u3:
            u3 = User(name='Finance Lead', email='finance@ftl.com', role='operation_executive', department='finance', status='active', password_hash=hashed)
            db.session.add(u3)
            print("Created new Finance Lead user.")
        else:
            u3.status = 'active'
            u3.password_hash = hashed
            print("Updated existing Finance Lead to Active.")
            
        # Ensure Export Manager exists and is active
        u4 = User.query.filter_by(email='export@ftl.com').first()
        if not u4:
            u4 = User(name='Export Manager', email='export@ftl.com', role='operation_executive', department='export', status='active', password_hash=hashed)
            db.session.add(u4)
            print("Created new Export Manager user.")
        else:
            u4.status = 'active'
            u4.password_hash = hashed
            print("Updated existing Export Manager to Active.")
            
        db.session.commit()
        
        # Re-fetch IDs just in case
        fid = u3.id
        eid = u4.id
        
        # Populate / Link companies
        companies = Company.query.all()
        print(f"Linking {len(companies)} active companies...")
        for idx, company in enumerate(companies):
            if idx % 2 == 0:
                company.assigned_ops_id = fid
            else:
                company.assigned_ops_id = eid
        
        db.session.commit()
        print("SUCCESS: Both executive nodes are fully populated, active, and mapped to client entities!")

if __name__ == '__main__':
    run()
