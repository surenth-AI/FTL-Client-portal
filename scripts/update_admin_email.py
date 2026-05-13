import os
from app import create_app, db
from app.models.models import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(role='admin').first()
    if admin:
        print(f"Updating admin: {admin.email} -> admin@portal.com")
        admin.email = 'admin@portal.com'
        db.session.commit()
        print("Admin user updated successfully.")
    else:
        print("Admin user not found.")
