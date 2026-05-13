import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\LCL Rates Export 01022026-28022026 Nordic.xlsx"
xl = pd.ExcelFile(path)
df = pd.read_excel(xl, sheet_name="Default Rates")
print("Headers:", df.columns.tolist())
print("First 10 rows:")
print(df.head(10))
