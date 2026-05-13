import os
from app import create_app, db
from app.services.excel_importer import ExcelImporter

app = create_app()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder = os.path.join(BASE_DIR, 'Sample csv')
files = [
    "LCL Rates Export 01022026-28022026 Nordic.xlsx",
    "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx",
    # Ignoring TEAM FREIGHT for now as it's a diff format, focusing on the first two
]

with app.app_context():
    for filename in files:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            print(f"Importing {filename}...")
            with open(path, "rb") as f:
                content = f.read()
                result = ExcelImporter.process_file(content, filename)
                print(f"Result: {result['message']}")
        else:
            print(f"File not found: {path}")
