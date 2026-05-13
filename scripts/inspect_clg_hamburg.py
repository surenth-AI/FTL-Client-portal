import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
xl = pd.ExcelFile(path)
print(f"Sheets: {xl.sheet_names}")

for sheet in xl.sheet_names:
    print(f"\n--- Sheet: {sheet} ---")
    df = pd.read_excel(path, sheet_name=sheet, nrows=30)
    print("Columns:", df.columns.tolist())
    print("First 20 rows:")
    print(df.head(20))
