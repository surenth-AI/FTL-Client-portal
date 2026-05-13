import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime, timedelta
import random

def generate_pdf_invoice(filepath, supplier, inv_no, amount, currency, items):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFillColor(colors.HexColor("#1e222d"))
    c.rect(0, height - 100, width, 100, fill=1)
    
    c.setFillColor(colors.HexColor("#8b5cf6"))
    c.circle(60, height - 50, 30, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(45, height - 58, supplier[:2].upper())
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(110, height - 45, f"{supplier} Global")
    c.setFont("Helvetica", 10)
    c.drawString(110, height - 60, "Maritime Plaza, Terminal 4, Logistics Zone")
    c.drawString(110, height - 75, f"contact@{supplier.lower().replace(' ', '')}.com")
    
    # Invoice Title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.drawRightString(width - 50, height - 150, "TAX INVOICE")
    
    # Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 180, "BILL TO:")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 200, "AxeGlobal Logistics Solutions")
    c.drawString(50, height - 215, "Unified Freight Management Division")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 150, height - 180, "INVOICE DATA:")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 200, f"Invoice #: {inv_no}")
    c.drawRightString(width - 50, height - 215, f"Date: {datetime.utcnow().strftime('%B %d, %Y')}")
    c.drawRightString(width - 50, height - 230, f"Currency: {currency}")
    
    # Table Header
    c.setFillColor(colors.HexColor("#f3f4f6"))
    c.rect(50, height - 280, width - 100, 25, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, height - 273, "Description")
    c.drawString(300, height - 273, "Quantity")
    c.drawString(400, height - 273, "Unit Price")
    c.drawRightString(width - 60, height - 273, "Total")
    
    # Items
    y = height - 300
    c.setFont("Helvetica", 10)
    for desc, qty, uprice in items:
        total = qty * uprice
        c.drawString(60, y, desc)
        c.drawString(300, y, str(qty))
        c.drawString(400, y, f"{uprice:,.2f}")
        c.drawRightString(width - 60, y, f"{total:,.2f}")
        y -= 25
    
    # Footer
    y -= 20
    c.line(350, y + 10, width - 50, y + 10)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y - 10, "GRAND TOTAL:")
    c.drawRightString(width - 60, y - 10, f"{currency} {amount:,.2f}")
    
    c.save()

def main():
    base_dir = "client_test_data"
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. VENDOR INVOICES
    inv_dir = os.path.join(base_dir, "Vendor_Invoices")
    os.makedirs(inv_dir, exist_ok=True)
    suppliers = ["Maersk Line", "MSC Mediterranean", "Evergreen Marine", "CMA CGM", "Hapag-Lloyd"]
    for i, supplier in enumerate(suppliers):
        inv_no = f"INV-TEST-{1000 + i}"
        amount = random.uniform(500, 5000)
        generate_pdf_invoice(
            os.path.join(inv_dir, f"{inv_no}.pdf"),
            supplier, inv_no, amount, "USD",
            [("Ocean Freight", 1, amount * 0.8), ("THC Destination", 1, amount * 0.2)]
        )
    print(f"Generated {len(suppliers)} Vendor Invoices in {inv_dir}")

    # 2. SOA STATEMENT
    soa_dir = os.path.join(base_dir, "SOA_Statements")
    os.makedirs(soa_dir, exist_ok=True)
    
    # Create a realistic SOA Excel
    # Row 9 is header, Data starts at Row 10
    rows = []
    # Header row (Row 9)
    header = ["", "", "", "", "", "", "", "", "", "Job No.", "Debit", "Credit", "Reference"]
    for i in range(20):
        job_no = f"JOB-{2026}-{100 + i}"
        debit = random.uniform(1000, 3000) if i % 2 == 0 else 0
        credit = random.uniform(1000, 3000) if i % 2 != 0 else 0
        rows.append([""]*9 + [job_no, debit, credit, f"REF-{i}"])
    
    df_soa = pd.DataFrame([[""]*13]*9 + [header] + rows)
    soa_path = os.path.join(soa_dir, "Vendor_Statement_Audit_Sample.xlsx")
    df_soa.to_excel(soa_path, index=False, header=False)
    print(f"Generated SOA Statement in {soa_dir}")

    # 3. EDI PRE-ALERTS
    edi_dir = os.path.join(base_dir, "EDI_PreAlerts")
    os.makedirs(edi_dir, exist_ok=True)
    edi_data = [
        {"MBL": "MAEU123456789", "HBL": "HBL-001", "Container": "MSCU1234567", "Weight": 12500, "Packages": 150, "CBM": 22.5},
        {"MBL": "MSCU987654321", "HBL": "HBL-002", "Container": "MAEU7654321", "Weight": 8900, "Packages": 80, "CBM": 12.0},
    ]
    df_edi = pd.DataFrame(edi_data)
    df_edi.to_excel(os.path.join(edi_dir, "PreAlert_Manifest_Sample.xlsx"), index=False)
    print(f"Generated EDI Pre-Alerts in {edi_dir}")

    # 4. RATES SHEET
    rates_dir = os.path.join(base_dir, "Rates")
    os.makedirs(rates_dir, exist_ok=True)
    rates_data = [
        {"Origin": "Shanghai", "Destination": "Hamburg", "Carrier": "Maersk", "20GP": 1200, "40HC": 2100, "Currency": "USD", "Validity": "2026-12-31"},
        {"Origin": "Ningbo", "Destination": "Felixstowe", "Carrier": "MSC", "20GP": 1150, "40HC": 2050, "Currency": "USD", "Validity": "2026-12-31"},
        {"Origin": "Singapore", "Destination": "Rotterdam", "Carrier": "Evergreen", "20GP": 900, "40HC": 1600, "Currency": "USD", "Validity": "2026-12-31"},
    ]
    df_rates = pd.DataFrame(rates_data)
    df_rates.to_excel(os.path.join(rates_dir, "Global_Ocean_Rates_2026.xlsx"), index=False)
    print(f"Generated Rates Sheet in {rates_dir}")

if __name__ == "__main__":
    main()
