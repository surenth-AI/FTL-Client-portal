import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.services.excel_importer import ExcelImporter
from app.models.models import Rate

app = create_app()
filename = 'Sample csv/TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx'

if not os.path.exists(filename):
    print(f"File not found: {filename}")
else:
    with open(filename, 'rb') as f:
        content = f.read()

    with app.app_context():
        # Clear old rates for this test
        Rate.query.filter_by(nvocc_name='Team Freight').delete()
        db.session.commit()
        
        result = ExcelImporter.process_file(content, filename)
        print(f"Result: {result}")
        
        # Verify the data
        rate = Rate.query.filter_by(nvocc_name='Team Freight').first()
        if rate:
            print(f"Imported Rate: {rate.origin} -> {rate.destination}")
            print(f"Base Rate: {rate.base_rate}, Surcharges: {rate.surcharges}, Transit: {rate.transit_days}")
            print(f"Validity: {rate.validity_start} to {rate.validity_end}")
        else:
            print("No rate found in DB!")
