import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.services.excel_importer import ExcelImporter
import os

# Create app and context
app = create_app()

with app.app_context():
    file_path = r"d:\AXE Global\ntex\Sample csv\TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
    # Test with the filename as passed by the user (which failed before)
    filename = "team freight as 01-03-2026 - 31-03-2026.xlsx"

    with open(file_path, 'rb') as f:
        content = f.read()

    print(f"Testing detection for filename: '{filename}'")
    result = ExcelImporter.process_file(content, filename)
    print(f"Result: {result}")

    if result['success']:
        # Double check the DB
        from app.models.models import Rate
        latest = Rate.query.filter_by(nvocc_name="Team Freight").order_by(Rate.id.desc()).first()
        if latest:
            print(f"Verified DB Entry: {latest.origin} -> {latest.destination}, Rate: {latest.base_rate}, Surcharges: {latest.surcharges}")
        else:
            print("Error: Success reported but no DB entry found.")
