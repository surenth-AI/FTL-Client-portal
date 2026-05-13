import pandas as pd
import os
import re

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv')
nordic_file = "LCL Rates Export 01022026-28022026 Nordic.xlsx"
team_file = "TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
clg_file = "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"

def normalize(s):
    # Remove everything in parentheses, then remove non-alphanumeric, then strip
    s = str(s).split('(')[0]
    return re.sub(r'[^A-Z0-9]', '', s.upper()).strip()

def get_nordic_destinations():
    try:
        df = pd.read_excel(os.path.join(folder, nordic_file), sheet_name='LCL Export Rates', skiprows=4)
        col = 'Port of Discharge'
        if col not in df.columns: col = 'Unnamed: 4'
        vals = df[col].dropna().astype(str).tolist()
        return {normalize(v): v for v in vals}
    except Exception as e:
        print(f"Error Nordic: {e}")
        return {}

def get_team_destinations():
    try:
        df = pd.read_excel(os.path.join(folder, team_file), sheet_name='Ports')
        col = 'PortOfDischarge'
        vals = df[col].dropna().astype(str).tolist()
        return {normalize(v): v for v in vals}
    except Exception as e:
        print(f"Error Team: {e}")
        return {}

def get_clg_destinations():
    try:
        df = pd.read_excel(os.path.join(folder, clg_file), sheet_name='LCL Oceanfreight- Export', skiprows=19)
        col = 'Port'
        if col not in df.columns: col = 'Unnamed: 1'
        vals = df[col].dropna().astype(str).tolist()
        return {normalize(v): v for v in vals}
    except Exception as e:
        print(f"Error CLG: {e}")
        return {}

n_map = get_nordic_destinations()
t_map = get_team_destinations()
c_map = get_clg_destinations()

print(f"\nExtracted Destinations:")
print(f"Nordic: {len(n_map)}")
print(f"Team: {len(t_map)}")
print(f"CLG: {len(c_map)}")

common_all = set(n_map.keys()).intersection(t_map.keys()).intersection(c_map.keys())
print(f"\nCommon in ALL 3 providers: {len(common_all)}")
for k in sorted(list(common_all)):
    print(f"- {n_map[k]} | {t_map[k]} | {c_map[k]}")

common_nt = set(n_map.keys()).intersection(t_map.keys())
common_nc = set(n_map.keys()).intersection(c_map.keys())
common_tc = set(t_map.keys()).intersection(c_map.keys())

print(f"\nOverlaps Summary:")
print(f"- Nordic & Team: {len(common_nt)}")
print(f"- Nordic & CLG: {len(common_nc)}")
print(f"- Team & CLG: {len(common_tc)}")
