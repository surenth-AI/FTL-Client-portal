import os
import pandas as pd
from app import create_app, db
from app.services.excel_importer import ExcelImporter
from app.models.models import Rate

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv')
files = [
    "LCL Rates Export 01022026-28022026 Nordic.xlsx",
    "TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx",
    "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
]

app = create_app()
with app.app_context():
    # Clear any rates that might have been seeded/uploaded
    Rate.query.delete()
    db.session.commit()
    print("Cleared existing rates.")

    for filename in files:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            print(f"Uploading {filename}...")
            with open(path, 'rb') as f:
                content = f.read()
                result = ExcelImporter.process_file(content, filename)
                print(f"Result: {result['message']}")
        else:
            print(f"File not found: {filename}")
    
    total = Rate.query.count()
    print(f"\nFinal Rate Count in Database: {total}")
