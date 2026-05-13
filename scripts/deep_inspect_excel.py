import pandas as pd
import os

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv')
files = [
    "LCL Rates Export 01022026-28022026 Nordic.xlsx",
    "TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx",
    "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
]

for file in files:
    path = os.path.join(folder, file)
    print(f"\n==================================================")
    print(f"FILE: {file}")
    print(f"==================================================")
    try:
        xl = pd.ExcelFile(path)
        print(f"Sheets: {xl.sheet_names}")
        for sheet_name in xl.sheet_names:
            print(f"\n--- Sheet: {sheet_name} (first 10 rows) ---")
            df = pd.read_excel(path, sheet_name=sheet_name, nrows=10)
            print(df.to_string())
    except Exception as e:
        print(f"Error reading {file}: {e}")
