import pandas as pd
import os

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv')
nordic_file = "LCL Rates Export 01022026-28022026 Nordic.xlsx"
team_file = "TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
clg_file = "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"

def get_nordic_destinations():
    try:
        # Based on previous deep inspect, the data starts around row 7
        df = pd.read_excel(os.path.join(folder, nordic_file), sheet_name='LCL Export Rates', skiprows=6)
        # Search for a column that looks like 'Destination'
        dest_col = None
        for col in df.columns:
            if 'destination' in str(col).lower() or 'port' in str(col).lower():
                dest_col = col
                break
        if dest_col:
            return set(df[dest_col].dropna().astype(str).str.upper().str.strip())
        return set()
    except Exception as e:
        print(f"Error reading Nordic: {e}")
        return set()

def get_team_destinations():
    try:
        df = pd.read_excel(os.path.join(folder, team_file), sheet_name='Ports')
        if 'PortOfDischarge' in df.columns:
            return set(df['PortOfDischarge'].dropna().astype(str).str.upper().str.strip())
        return set()
    except Exception as e:
        print(f"Error reading Team Freight: {e}")
        return set()

def get_clg_destinations():
    try:
        # CLG Hamburg has the table starting later, let's find it.
        # It's 'LCL Oceanfreight- Export'
        df = pd.read_excel(os.path.join(folder, clg_file), sheet_name='LCL Oceanfreight- Export', skiprows=5)
        # Found in deep inspect: Unnamed: 0 looks like destination
        first_col = df.columns[0]
        return set(df[first_col].dropna().astype(str).str.upper().str.strip())
    except Exception as e:
        print(f"Error reading CLG: {e}")
        return set()

nordic_dests = get_nordic_destinations()
team_dests = get_team_destinations()
clg_dests = get_clg_destinations()

print(f"\nNordic Destinations Count: {len(nordic_dests)}")
print(f"Team Freight Destinations Count: {len(team_dests)}")
print(f"CLG Hamburg Destinations Count: {len(clg_dests)}")

# Normalize strings to improve matching (remove punctuation, extra spaces)
import re
def normalize(s):
    return re.sub(r'[^A-Z0-9 ]', '', s.upper())

n_norm = {normalize(d): d for d in nordic_dests}
t_norm = {normalize(d): d for d in team_dests}
c_norm = {normalize(d): d for d in clg_dests}

common_keys = set(n_norm.keys()).intersection(set(t_norm.keys())).intersection(set(c_norm.keys()))

print(f"\nCommon destinations in ALL 3 providers: {len(common_keys)}")
for k in list(common_keys)[:15]:
    print(f"- {n_norm[k]} (Nordic) / {t_norm[k]} (Team) / {c_norm[k]} (CLG)")

common_nt = set(n_norm.keys()).intersection(set(t_norm.keys()))
common_nc = set(n_norm.keys()).intersection(set(c_norm.keys()))
common_tc = set(t_norm.keys()).intersection(set(c_norm.keys()))

print(f"\nOverlaps:")
print(f"- Nordic & Team Freight: {len(common_nt)} common destinations")
print(f"- Nordic & CLG-Hamburg: {len(common_nc)} common destinations")
print(f"- Team Freight & CLG-Hamburg: {len(common_tc)} common destinations")
