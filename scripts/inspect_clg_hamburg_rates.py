import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
xl = pd.ExcelFile(path)

print("\n--- Sheet: LCL Oceanfreight- Export ---")
df = pd.read_excel(path, sheet_name="LCL Oceanfreight- Export")
print(df.head(50))
