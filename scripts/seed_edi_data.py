import os
import sys
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.models import EdiPreAlert

def seed_edi_data():
    print("Seeding bulk EDI data...")
    
    shippers = ["Global Electronics Ltd", "TechParts Manufacturing", "Nordic Paper Mills", "Asia Textiles Co", "Euro Motors GmbH"]
    consignees = ["TechStream Corp", "Nordic Imports Oy", "Global Trading Ltd", "EuroTrans GmbH", "Retail Group Inc"]
    vessels = ["MAERSK SEOUL", "CMA CGM ANTOINE", "MSC ISABELLA", "COSCO SHIPPING ARIES", "EVER GIVEN", "HMM ALGECIRAS"]
    ports = ["Shanghai", "Ningbo", "Shenzhen", "Hamburg", "Rotterdam", "Antwerp", "Felixstowe", "Jebel Ali", "New York"]
    
    statuses = ["parsed", "parsed", "parsed", "parsed", "error", "quarantined"]
    sources = ["API", "API", "SFTP", "email"]
    
    edi_records = []
    
    for i in range(1, 45):  # Create 44 EDI records
        pol = random.choice(ports[:4])
        pod = random.choice(ports[4:])
        status = random.choice(statuses)
        
        edi = EdiPreAlert(
            mbl_number=f"MBL{random.randint(1000000, 9999999)}",
            hbl_number=f"HBL-{random.randint(100000, 999999)}",
            vessel_name=random.choice(vessels),
            voyage_number=f"{random.randint(100, 999)}E",
            port_of_loading=pol,
            port_of_discharge=pod,
            eta_pod=datetime.utcnow() + timedelta(days=random.randint(5, 30)),
            shipper_name=random.choice(shippers),
            consignee_name=random.choice(consignees),
            cargo_description="GENERAL CARGO STC",
            weight_kg=random.uniform(5000, 25000),
            volume_cbm=random.uniform(10, 65),
            source_type=random.choice(sources),
            parse_status=status,
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
        )
        edi_records.append(edi)
        
    db.session.add_all(edi_records)
    db.session.commit()
    print(f"Successfully seeded {len(edi_records)} EDI records.")

def generate_edi_files():
    print("Generating sample EDI text files...")
    directory = 'sample_data/edi_samples'
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    for i in range(1, 6):
        edi_sample = f"""SHIPMENT PRE-ALERT
------------------
MBL: MSKU{random.randint(1000000, 9999999)}
HBL: HBL-{random.randint(100000, 999999)}
VESSEL: {random.choice(["MAERSK MC-KINNEY MOLLER", "MSC GULSUN", "CMA CGM JACQUES SAADE"])}
VOYAGE: {random.randint(100, 999)}W
POL: SHANGHAI
POD: HAMBURG
CONSIGNEE: GLOBAL TRADING LTD
NOTIFY: HAMBURG PORT AGENT
CARGO: 1 x 40HC STC ELECTRONIC COMPONENTS
WEIGHT: {random.randint(15000, 25000)} KGS
VOLUME: {random.randint(50, 70)} CBM
"""
        with open(os.path.join(directory, f'prealert_00{i}.txt'), 'w') as f:
            f.write(edi_sample)
            
    print(f"Created 5 sample EDI text files in {directory}/")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Optional: delete existing EDI records first to keep it clean
        EdiPreAlert.query.delete()
        db.session.commit()
        
        seed_edi_data()
        generate_edi_files()
