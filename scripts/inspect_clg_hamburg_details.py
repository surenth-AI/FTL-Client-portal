import pandas as pd
import os
import sys
sys.path.append(os.getcwd())

file_path = r"d:\AXE Global\ntex\Sample csv\TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
xl = pd.ExcelFile(file_path)

# Check sheet names
print(f"Sheet names: {xl.sheet_names}")

# Read first sheet
df = pd.read_excel(xl, sheet_name=0, header=None)
print("First sheet 'Calculator' snippet:")
print(df.iloc[9:16, 0:10]) # Rows around 10-15, columns around A-J

# Check validity dates
print(f"Cell (9, 7): {df.iloc[9, 7]}")
print(f"Cell (10, 7): {df.iloc[10, 7]}")

# Check Origin/Destination
print(f"Cell (10, 1): {df.iloc[10, 1]}")
print(f"Cell (12, 1): {df.iloc[12, 1]}")

# Check Base Rate
print(f"Cell (13, 7): {df.iloc[13, 7]}")

# Check Surcharges (Rows 26-40, Col 4)
print("Surcharges snippet (Col 4):")
print(df.iloc[25:46, 4])
