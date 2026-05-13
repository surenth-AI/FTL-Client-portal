import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
xl = pd.ExcelFile(path)
first_sheet = xl.sheet_names[0]
print(f"Inspecting first sheet: {first_sheet}")

df = pd.read_excel(path, sheet_name=first_sheet)
# Print rows where 'Port of Destination' might be
for i, row in df.iterrows():
    if "Port of Destination" in str(row.values):
        print(f"Header found at row {i}")
        print(df.iloc[i:i+10])
        break
