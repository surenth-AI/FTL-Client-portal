from app import create_app, db
from app.models.models import Rate
from datetime import date

app = create_app()

with app.app_context():
    # Clear existing Singapore-LA if any (to prevent duplicates)
    Rate.query.filter_by(origin='Singapore', destination='Los Angeles').delete()
    
    # Add 3 distinct options
    r1 = Rate(
        origin='Singapore', 
        destination='Los Angeles', 
        nvocc_name='Maersk', 
        base_rate=920.0, 
        surcharges=150.0, 
        transit_days=18, 
        validity_start=date(2026, 1, 1), 
        validity_end=date(2026, 12, 31)
    )
    r2 = Rate(
        origin='Singapore', 
        destination='Los Angeles', 
        nvocc_name='MSC', 
        base_rate=850.0, 
        surcharges=200.0, 
        transit_days=22, 
        validity_start=date(2026, 1, 1), 
        validity_end=date(2026, 12, 31)
    )
    r3 = Rate(
        origin='Singapore', 
        destination='Los Angeles', 
        nvocc_name='HMM', 
        base_rate=980.0, 
        surcharges=120.0, 
        transit_days=16, 
        validity_start=date(2026, 1, 1), 
        validity_end=date(2026, 12, 31)
    )
    
    db.session.add_all([r1, r2, r3])
    db.session.commit()
    print("Successfully added 3 sample rates for Singapore -> Los Angeles.")
