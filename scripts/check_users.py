from app import create_app, db
from app.models.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"User: {user.email}, Role: {user.role}")
