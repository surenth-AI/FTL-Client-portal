import os
import sys
from datetime import datetime, timedelta
import random

# Ensure parent path is accessible for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.models import Rate

def seed_freight_rates():
    app = create_app()
    with app.app_context():
        print("Cleaning existing freight rates...")
        db.session.query(Rate).delete()
        db.session.commit()
        
        origins = [
            'Shanghai (CNSHA)', 
            'Singapore (SGPIN)', 
            'Ningbo (CNNGB)', 
            'Jebel Ali (AEJEA)', 
            'Hong Kong (HKHKG)', 
            'Shenzhen (CNSZX)'
        ]
        
        destinations = [
            'Hamburg (DEHAM)', 
            'Rotterdam (NLRTM)', 
            'Antwerp (BEANR)', 
            'Los Angeles (USLAX)', 
            'New York (USNYC)', 
            'Felixstowe (GBFXT)'
        ]
        
        carriers = [
            ('Maersk Line', 'MAEU'),
            ('MSC Mediterranean', 'MSCU'),
            ('CMA CGM', 'CMAC'),
            ('COSCO Shipping', 'COSU'),
            ('Hapag-Lloyd', 'HLAG'),
            ('Evergreen Marine', 'EGLV'),
            ('ONE Ocean Network', 'ONEU'),
            ('OOCL Logistics', 'OOLU')
        ]
        
        rate_count = 0
        
        print("Seeding premium FCL and LCL rates...")
        for origin in origins:
            for dest in destinations:
                # Seed 2-4 competitive rates per origin-destination pair
                num_rates = random.randint(2, 4)
                chosen_carriers = random.sample(carriers, num_rates)
                
                for carrier_name, carrier_code in chosen_carriers:
                    # 1. Seed LCL rate
                    lcl_rate = Rate(
                        origin=origin,
                        destination=dest,
                        nvocc_name=carrier_name,
                        carrier_name=carrier_code,
                        base_rate=float(random.randint(65, 140)), # Base LCL rate per CBM
                        surcharges=float(random.randint(90, 180)), # Port/fuel surcharges
                        transit_days=random.randint(18, 38),
                        validity_start=datetime.utcnow().date(),
                        validity_end=(datetime.utcnow() + timedelta(days=90)).date(),
                        service_type='LCL'
                    )
                    db.session.add(lcl_rate)
                    
                    # 2. Seed FCL rate
                    fcl_rate = Rate(
                        origin=origin,
                        destination=dest,
                        nvocc_name=carrier_name,
                        carrier_name=carrier_code,
                        base_rate=float(random.randint(1200, 3200)), # Base FCL rate per container
                        surcharges=float(random.randint(350, 750)), # FCL port/security surcharges
                        transit_days=random.randint(18, 38),
                        validity_start=datetime.utcnow().date(),
                        validity_end=(datetime.utcnow() + timedelta(days=90)).date(),
                        service_type='FCL'
                    )
                    db.session.add(fcl_rate)
                    rate_count += 2
                    
        db.session.commit()
        print(f"SUCCESS: Successfully seeded {rate_count} dynamic freight rates in SQLite database!")

if __name__ == "__main__":
    seed_freight_rates()
