from app import create_app, db
from app.models.models import Rate, Booking, TrackingEvent, User

app = create_app()

with app.app_context():
    print("Starting database cleanup...")
    
    # 1. Clear Rates
    num_rates = Rate.query.count()
    Rate.query.delete()
    print(f" - Deleted {num_rates} rates.")
    
    # 2. Clear Bookings and Tracking Events
    num_events = TrackingEvent.query.count()
    TrackingEvent.query.delete()
    print(f" - Deleted {num_events} tracking events.")
    
    num_bookings = Booking.query.count()
    Booking.query.delete()
    print(f" - Deleted {num_bookings} bookings.")
    
    # 3. Commit changes
    db.session.commit()
    print("\nDatabase cleanup complete. Current counts:")
    print(f"Rates: {Rate.query.count()}")
    print(f"Bookings: {Booking.query.count()}")
    print(f"Users: {User.query.count()} (Preserved)")
