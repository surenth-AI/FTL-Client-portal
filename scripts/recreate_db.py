from app import create_app, db
import os

app = create_app()
with app.app_context():
    # Remove existing db if it exists
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'axeglobal.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed old database: {db_path}")
    
    db.create_all()
    print("Recreated database with updated schema.")
    
    # Re-seed the admin
    from app.__init__ import seed_admin
    seed_admin()
    print("Admin user re-seeded.")
