import pandas as pd
import os

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Sample csv')
nordic_file = "LCL Rates Export 01022026-28022026 Nordic.xlsx"
team_file = "TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
clg_file = "export rates February 2026 - (englisch) - CLG-Hamburg.xlsx"

def get_nordic_destinations():
    try:
        df = pd.read_excel(os.path.join(folder, nordic_file), sheet_name='Quotations', skiprows=6)
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
        df = pd.read_excel(os.path.join(folder, clg_file), skiprows=5)
        # The column for destination seems to be 'Unnamed: 0' or similar based on previous inspection
        # Let's try to find the row where 'Port of Destination' or similar is mentioned in the full raw load
        raw_df = pd.read_excel(os.path.join(folder, clg_file), nrows=20)
        dest_list = set()
        for idx, row in raw_df.iterrows():
            if 'destination' in str(row[0]).lower():
                # Table might start here
                actual_df = pd.read_excel(os.path.join(folder, clg_file), skiprows=idx+1)
                first_col = actual_df.columns[0]
                dest_list = set(actual_df[first_col].dropna().astype(str).str.upper().str.strip())
                break
        return dest_list
    except Exception as e:
        print(f"Error reading CLG: {e}")
        return set()

nordic_dests = get_nordic_destinations()
team_dests = get_team_destinations()
clg_dests = get_clg_destinations()

print(f"\nNordic Destinations Count: {len(nordic_dests)}")
print(f"Team Freight Destinations Count: {len(team_dests)}")
print(f"CLG Hamburg Destinations Count: {len(clg_dests)}")

common_all = nordic_dests.intersection(team_dests).intersection(clg_dests)
common_nordic_team = nordic_dests.intersection(team_dests)
common_nordic_clg = nordic_dests.intersection(clg_dests)
common_team_clg = team_dests.intersection(clg_dests)

print(f"\nCommon in ALL 3 providers: {len(common_all)}")
if common_all:
    print(list(common_all)[:10], "...")

print(f"\nCommon in Nordic & Team Freight: {len(common_nordic_team)}")
print(f"Common in Nordic & CLG-Hamburg: {len(common_nordic_clg)}")
print(f"Common in Team Freight & CLG-Hamburg: {len(common_team_clg)}")

unique_union = nordic_dests.union(team_dests).union(clg_dests)
print(f"\nTotal Unique Destinations across all: {len(unique_union)}")
