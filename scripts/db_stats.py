from app import create_app, db
from app.models.models import Rate, Booking, User, TrackingEvent

app = create_app()

with app.app_context():
    print(f"Rates: {Rate.query.count()}")
    print(f"Bookings: {Booking.query.count()}")
    print(f"Tracking Events: {TrackingEvent.query.count()}")
    print(f"Users: {User.query.count()}")
    
    # List users to see who is there
    users = User.query.all()
    for u in users:
        print(f" - {u.email} ({u.role})")
