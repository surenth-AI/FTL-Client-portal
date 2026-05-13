import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
xl = pd.ExcelFile(path)

print("\n--- Sheet: LCL Oceanfreight- Export (Rows 15-40) ---")
df = pd.read_excel(path, sheet_name="LCL Oceanfreight- Export")
print(df.iloc[15:40])
