import pandas as pd
import io
from datetime import datetime, date
from app.models.models import Rate
from app import db

class ExcelImporter:
    @staticmethod
    def process_file(file_content, filename):
        """
        Main entry point for handling different Excel formats.
        """
        try:
            xl = pd.ExcelFile(io.BytesIO(file_content))
            
            # Detect which file type it is based on sheet names and filename keywords
            sheet_names = [str(s).strip() for s in xl.sheet_names]
            fname_lower = filename.lower()

            if "Default Rates" in sheet_names and "Default TT" in sheet_names:
                return ExcelImporter._parse_nordic_matrix(xl, filename)
            elif "export rates" in fname_lower:
                return ExcelImporter._parse_clg_hamburg(xl, filename)
            elif "team freight" in fname_lower or "Calculator" in sheet_names:
                return ExcelImporter._parse_team_freight(xl, filename)
            else:
                # Generic fallback if sheet detection fails
                return {"success": False, "message": f"Format detection failed for {filename}. Available sheets: {sheet_names}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def _parse_nordic_matrix(xl, filename):
        """
        Handles the 'Nordic' format: Origins in columns, Destinations in rows.
        Enhanced to capture carrier and frequency information.
        """
        sheet_name = 'LCL Export Rates'
        if sheet_name not in xl.sheet_names:
            return {"success": False, "message": f"Sheet '{sheet_name}' not found for Nordic format."}
            
        # Header is usually at row 4 (index 4)
        df = pd.read_excel(xl, sheet_name=sheet_name, skiprows=4)
        
        # Columns mapping:
        # 'Port of Discharge' (Unnamed: 4), 'Port of Loading' (Unnamed: 6), 'Rate w/m' (Unnamed: 8), 'TT' (Unnamed: 11), 'Freq.' (Unnamed: 10)
        
        count = 0
        for _, row in df.iterrows():
            dest = str(row.get('Port of Discharge', row.iloc[4])).strip()
            if not dest or dest == 'nan': continue
            
            origin = str(row.get('Port of Loading', row.iloc[6])).strip()
            if not origin or origin == 'nan' or origin == 'Port of Loading': continue
            
            try:
                base_rate = float(row.get('Rate w/m', row.iloc[8]))
                surcharges = 45.0 # Average default
                transit_days = int(float(row.get('TT', row.iloc[11])))
                freq = str(row.get('Freq.', row.iloc[10])).strip()
                
                imo_status = str(row.iloc[14]).strip()
                remark_val = str(row.iloc[15]).strip()
                remark_text = f"{remark_val}" if remark_val != 'nan' else ""
                if imo_status != 'nan' and imo_status.lower() != 'no':
                    remark_text += f" | IMO: {imo_status}"
                
                new_rate = Rate(
                    origin=origin,
                    destination=dest,
                    nvocc_name="Nordic",
                    carrier_name="Carrier Direct/T/S",
                    frequency=freq,
                    base_rate=base_rate,
                    surcharges=surcharges,
                    transit_days=transit_days,
                    validity_start=date(2026, 2, 1),
                    validity_end=date(2026, 2, 28),
                    remarks=remark_text
                )
                db.session.add(new_rate)
                count += 1
            except:
                continue

        db.session.commit()
        return {"success": True, "message": f"Successfully imported {count} rates from {filename}."}

    @staticmethod
    def _parse_clg_hamburg(xl, filename):
        """
        Handles the CLG-Hamburg format by targeting the 'Eingabemaske Raten' sheet.
        Deep import: Sums up all specific surcharge columns (EU ETS, BAF, Panama, etc.).
        """
        sheet_name = "Eingabemaske Raten"
        if sheet_name not in xl.sheet_names:
            # Fallback to general sheet if Eingabemaske not found
            sheet_name = "LCL Oceanfreight- Export"
        
        # Row 2 is the header
        df = pd.read_excel(xl, sheet_name=sheet_name, skiprows=2)
        
        count = 0
        for _, row in df.iterrows():
            dest = str(row.iloc[1]).strip() # Col B: Hafenplatz
            if not dest or dest == 'nan' or dest == 'Hafenplatz': continue
            
            try:
                base_rate = float(row.iloc[3]) # Col D: Rate
                
                # Summing all surcharges
                # Col F: Emergency, Col G: EU ETS, Col H: Baf, Col I: Panama, Col J: Umladung
                surcharge_total = 0.0
                for col_idx in [5, 6, 7, 8, 9]:
                    try:
                        val = row.iloc[col_idx]
                        if not pd.isna(val):
                            surcharge_total += float(val)
                    except:
                        pass
                
                tt_val = int(row.iloc[10]) if not pd.isna(row.iloc[10]) else 20
                remarks = str(row.iloc[11]) if not pd.isna(row.iloc[11]) else ""
                
                new_rate = Rate(
                    origin="Hamburg",
                    destination=dest,
                    nvocc_name="CLG Hamburg",
                    carrier_name="CLG Deep/Direct",
                    frequency="Weekly",
                    base_rate=base_rate,
                    surcharges=surcharge_total,
                    transit_days=tt_val,
                    validity_start=date(2026, 2, 1),
                    validity_end=date(2026, 2, 28),
                    remarks=remarks
                )
                db.session.add(new_rate)
                count += 1
            except:
                continue
            
        db.session.commit()
        return {"success": True, "message": f"Successfully imported {count} rates (v3 deep) from CLG data."}

    @staticmethod
    def _parse_team_freight(xl, filename):
        """
        Handles the 'Team Freight' format: Bulk import from 'Ocean Freight' 
        with surcharge cross-referencing from 'Surcharges' sheet.
        """
        if 'Ocean Freight' not in xl.sheet_names:
            return {"success": False, "message": "Sheet 'Ocean Freight' not found for Team Freight."}
            
        # Load Surcharges into dynamic lookup
        surcharge_map = {}
        if 'Surcharges' in xl.sheet_names:
            sur_df = pd.read_excel(xl, sheet_name='Surcharges', skiprows=11)
            for _, srow in sur_df.iterrows():
                code = str(srow.get('Code', srow.iloc[3])).strip()
                if not code or code == 'nan': continue
                
                try:
                    desc = str(srow.get('Description', srow.iloc[6])).strip().upper()
                    rate = srow.get('Rate', srow.iloc[8])
                    
                    if code not in surcharge_map: surcharge_map[code] = {'total': 0.0, 'notes': []}
                    
                    if isinstance(rate, (int, float)):
                        surcharge_map[code]['total'] += float(rate)
                        surcharge_map[code]['notes'].append(f"{desc}: {rate}")
                    elif str(rate).upper() == 'ON REQUEST':
                        surcharge_map[code]['notes'].append(f"{desc}: ON REQUEST")
                except:
                    continue

        # Process Ocean Freight
        df = pd.read_excel(xl, sheet_name='Ocean Freight', skiprows=15, header=None)
        
        count = 0
        for _, row in df.iterrows():
            dest = str(row.iloc[0]).strip()
            if not dest or dest == 'nan' or dest == 'OCEAN FREIGHT': continue
            
            code = str(row.iloc[2]).strip() # Col C: Port Code
            
            try:
                rate_val = row.iloc[6] # Col G: Rate
                tt_val = row.iloc[8] # Col I: TT
                
                if pd.isna(rate_val): continue
                
                # Fetch port-specific surcharges
                port_sur = surcharge_map.get(code, {'total': 25.0, 'notes': []})
                
                new_rate = Rate(
                    origin="Antwerp/Rotterdam",
                    destination=dest,
                    nvocc_name="Team Freight",
                    carrier_name="Direct/TS Carrier",
                    frequency="Weekly",
                    base_rate=float(rate_val),
                    surcharges=float(port_sur['total']),
                    transit_days=int(tt_val) if not pd.isna(tt_val) else 21,
                    validity_start=date(2026, 3, 1),
                    validity_end=date(2026, 3, 31),
                    remarks=" | ".join(port_sur['notes'][:3]) or (f"Via {row.iloc[3]}" if not pd.isna(row.iloc[3]) else "")
                )
                db.session.add(new_rate)
                count += 1
            except:
                continue
                
        db.session.commit()
        return {"success": True, "message": f"Successfully imported {count} rates (v3 deep) from Team Freight."}
