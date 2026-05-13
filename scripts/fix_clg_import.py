import os
from app import create_app, db
from app.models.models import Rate
from app.services.excel_importer import ExcelImporter

app = create_app()

filename = "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
path = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv'), filename)

with app.app_context():
    print(f"Cleaning up old CLG Hamburg data...")
    # Delete old, incorrect records
    deleted = Rate.query.filter_by(nvocc_name='CLG Hamburg').delete()
    print(f" - Removed {deleted} incorrect records.")
    
    if os.path.exists(path):
        print(f"Re-importing {filename}...")
        with open(path, "rb") as f:
            content = f.read()
            result = ExcelImporter.process_file(content, filename)
            print(f"Result: {result['message']}")
    else:
        print(f"File not found: {path}")
    
    db.session.commit()

# Final check
with app.app_context():
    count = Rate.query.filter_by(nvocc_name='CLG Hamburg').count()
    print(f"\nFinal count for CLG Hamburg: {count} records successfully imported.")
