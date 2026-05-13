import pandas as pd
import os

file_path = r"d:\AXE Global\ntex\Sample csv\TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
filename = os.path.basename(file_path).lower()

print(f"Testing filename: '{filename}'")
print(f"Condition 'team freight' in filename: {'team freight' in filename}")

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheet names: {xl.sheet_names}")
except Exception as e:
    print(f"Error reading Excel: {e}")
