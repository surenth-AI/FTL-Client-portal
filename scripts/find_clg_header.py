import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
xl = pd.ExcelFile(path)

df = pd.read_excel(path, sheet_name="LCL Oceanfreight- Export")

# Let's find any row that has "Port" or "Destination" or "USD"
for i, row in df.iterrows():
    row_str = " ".join([str(x) for x in row.values]).lower()
    if "port" in row_str or "destination" in row_str or "usd" in row_str:
        print(f"Potential header at row {i}:")
        print(row.values)
        if i < len(df) - 5:
            print("Next few rows:")
            print(df.iloc[i+1:i+5])
        print("-" * 20)
