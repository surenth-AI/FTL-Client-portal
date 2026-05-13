import pandas as pd
import os

path = r"d:\AXE Global\ntex\Sample csv\export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"
xl = pd.ExcelFile(path)

print("\n--- Sheet: Mitarbeiter & Häfen & TT ---")
df_ports = pd.read_excel(path, sheet_name="Mitarbeiter & Häfen & TT")
print(df_ports.head(50))

print("\n--- Sheet: Eingabemaske Raten ---")
df_rates = pd.read_excel(path, sheet_name="Eingabemaske Raten")
print(df_rates.head(50))
