from app import create_app
from app.models.models import Rate

app = create_app()

with app.app_context():
    print(f"Total rates in database: {Rate.query.count()}")
    
    # Check for anything starting with Singapore as Origin
    singapore_origin = Rate.query.filter(Rate.origin.like('%Singapore%')).all()
    print(f"\nRates from Singapore: {len(singapore_origin)}")
    for r in singapore_origin[:5]:
        print(f" - {r.origin} -> {r.destination} (${r.base_rate})")
        
    # Check for anything matching Los Angeles as Destination
    la_dest = Rate.query.filter(Rate.destination.like('%Los Angeles%')).all()
    print(f"\nRates to Los Angeles: {len(la_dest)}")
    for r in la_dest[:5]:
        print(f" - {r.origin} -> {r.destination} (${r.base_rate})")
        
    # Check why EXACT match for Singapore -> Los Angeles might fail
    exact = Rate.query.filter_by(origin='Singapore', destination='Los Angeles').all()
    print(f"\nExact match Singapore -> Los Angeles: {len(exact)}")
