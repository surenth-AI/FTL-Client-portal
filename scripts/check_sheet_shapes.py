import pandas as pd
import os

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv')
files = [
    ("LCL Rates Export 01022026-28022026 Nordic.xlsx", "LCL Export Rates"),
    ("TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx", "Ports"),
    ("export rates February 2026 - (englisch) - CLG-Hamburg.xlsx", "LCL Oceanfreight- Export")
]

for file_name, sheet_name in files:
    path = os.path.join(folder, file_name)
    print(f"\nFILE: {file_name} | SHEET: {sheet_name}")
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, nrows=30)
        print(df.to_string())
    except Exception as e:
        print(f"Error: {e}")
