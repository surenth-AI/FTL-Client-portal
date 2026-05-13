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
    print(f"\n--- {file} ---")
    try:
        df = pd.read_excel(path, nrows=5)
        print("Columns:", df.columns.tolist())
        print("Rows:")
        print(df.head())
    except Exception as e:
        print(f"Error reading {file}: {e}")
