from app import create_app, db
from app.models.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Delete existing admin if any
    User.query.filter_by(role='admin').delete()
    
    # Create fresh admin
    admin = User(
        name='System Admin',
        email='admin@axeglobal.com',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin user reset to: admin@axeglobal.com / admin123")
