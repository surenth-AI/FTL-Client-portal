import os
import json
from google import genai
from google.genai import types
from flask import current_app

def parse_invoice_document(file_data, mime_type):
    """
    Uses the modern google-genai SDK to extract structured JSON from an invoice document.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)

    # Use the stable flash model
    model_id = "gemini-2.5-flash-lite" 

    prompt = """
    Extract structured data from this logistics invoice with INDUSTRIAL PRECISION. 
    Use the following strict HIERARCHY for references when determining the primary dossier identifier:
    PRIORITY: 1. Container Number, 2. BL Number, 3. HBL (House BL), 4. Reference Number, 5. MBL (Master BL), 6. AWB/Air Waybill.

    EXTRACTION RULES:
    1. EXTRACT ALL 15+ FIELDS listed below for every line item. Do not leave null if inferred.
    2. CLEAN NUMBERS: Remove currency symbols ($, €, €) and ensure amounts use dots (.) for decimals.
    3. REFERENCES: If a line item specifies a different dossier (e.g. specific HBL) than the header, capture it in the item's logistics fields.

    SCHEMA (REPLY ONLY WITH CLEAN JSON):
    - vendor_name: (Full vendor legal name).
    - supplier_code: (Supplier internal code if present).
    - invoice_number: (Invoice identifier).
    - invoice_date: (ISO format YYYY-MM-DD).
    - invoice_type: (Invoice, Credit Note, Fattura).
    - total_amount: (Float - Total Invoice Value).
    - currency: (3-letter code).
    - vat_amount: (Float - Total Tax).
    - vat_code: (Header level VAT code).
    - net_weight: (Float in KG).
    - gross_weight: (Float in KG).
    - job_reference: (The primary Job/Dossier Number linked to this invoice).
    - references: List of Objects (ref_type, ref_value, amount).
    - line_items: List of Objects:
        - description: (Commercial description).
        - quantity: (Float).
        - unit_price: (Float).
        - total_price: (Float).
        - currency: (3-letter code).
        - charge_code: (Internal cost/description code if available).
        - vat_code: (VAT code for this line).
        - vat_perc: (Float percentage).
        - vendor_code: (Line-specific vendor code).
        - vendor_name: (Line-specific vendor name).
        - job_id: (Dossier/Job ID for this specific line).
        - master_id: (Master reference for this specific line).
        - m_bl_no: (Master BL for this line).
        - h_bl_no: (House BL for this line).
        - container_no: (Container ID for this line).
        - awb_no: (Air Waybill for this line).
    - notes: (Internal AI confidence notes).
    """

    try:
        # Call the modern Gemini API
        response = client.models.generate_content(
            model=model_id,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=file_data,
                    mime_type=mime_type
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )

        # Log token usage
        if response.usage_metadata:
            print(f"AI Usage: Prompt={response.usage_metadata.prompt_token_count}, Response={response.usage_metadata.candidates_token_count}, Total={response.usage_metadata.total_token_count}")

        # If parsed object exists, use it. Otherwise, parse response.text manually.
        parsed_obj = getattr(response, 'parsed', None)
        if parsed_obj:
            return parsed_obj
            
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini Parsing Error: {e}")
        raise Exception(f"AI Parsing failed: {str(e)}")

def verify_invoice_match(invoice, extracted_data):
    """
    INDUSTRIAL AUDIT ENGINE:
    Cross-checks every line item against Job Estimates using multiple keys:
    (Charge Code > Vendor > Description)
    """
    from app.models.models import Job, EstimateItem
    
    # 1. Dossier Anchoring Logic
    REF_PRIORITY = {
        'Container Number': 1, 'BL Number': 2, 'HBL': 3, 'Reference': 4, 'MBL': 5, 'AWB': 6
    }
    
    search_entries = []
    if extracted_data.get('job_reference'):
        search_entries.append(('Reference', extracted_data['job_reference']))
    for ref in extracted_data.get('references', []):
        if ref.get('ref_value'):
            search_entries.append((ref.get('ref_type', 'Reference'), ref['ref_value']))
    
    search_entries.sort(key=lambda x: REF_PRIORITY.get(x[0], 99))
    search_values = [v for _, v in search_entries]
            
    if not search_values:
        return "ERROR: NO REFERENCES", None
    
    job = None
    for val in search_values:
        job = Job.query.filter_by(job_number=val).first()
        if job: break
    
    if not job:
        return f"UNANCHORED: {search_values[0]}", None
    
    # 2. Granular Line-Item Auditing
    ext_items = extracted_data.get('line_items', [])
    job_estimates = job.estimates # List[EstimateItem]
    
    if not ext_items:
        return "ERROR: NO DATA EXTRACTED", job.id
    if not job_estimates:
        return "PENDING: NO ESTIMATES", job.id

    results = {
        'total_lines': len(ext_items),
        'matched': 0,
        'overcharged': 0,
        'unexpected': 0,
        'vendor_mismatch': 0
    }
    
    for ext in ext_items:
        # Field Pre-Processing
        ext_code = (ext.get('charge_code') or "").upper()
        ext_desc = (ext.get('description') or "").upper()
        ext_vendor = (ext.get('vendor_name') or extracted_data.get('vendor_name') or "").upper()
        ext_price = 0.0
        try:
            ext_price = float(str(ext.get('total_price')).replace(',', '').strip())
        except: pass

        # Check for Smart Aggregation
        if ext_code == 'AGGREGATED':
            est_sum = sum(est.total for est in job_estimates)
            if ext_price > (est_sum + 0.05):
                results['overcharged'] += 1
                results['matched'] += 1 # We match the 'dossier' but price is high
            elif ext_price >= (est_sum - 0.05):
                results['matched'] += 1
            else:
                # Less priced than estimate
                results['matched'] += 1
            continue

        # Find best match in estimates
        best_match = None
        for est in job_estimates:
            est_code = (est.code or "").upper()
            est_desc = (est.description or "").upper()
            est_vendor = (est.entity_for or "").upper()
            
            # Match priority: Code > Vendor+Description > Fuzzy Description
            if est_code and ext_code and (est_code == ext_code):
                best_match = est
                break
            if est_vendor in ext_vendor and any(word in ext_desc for word in est_desc.split() if len(word) > 4):
                best_match = est
                break
        
        if best_match:
            results['matched'] += 1
            # Check for overcharge (0.05 tolerance for rounding)
            if ext_price > (best_match.total + 0.05):
                results['overcharged'] += 1
            # Check vendor consistency
            if best_match.entity_for and ext_vendor and best_match.entity_for.upper() not in ext_vendor:
                results['vendor_mismatch'] += 1
        else:
            results['unexpected'] += 1

    # 3. Final State Matrix
    if results['matched'] == results['total_lines']:
        if results['overcharged'] == 0:
            return "MATCHED 100%", job.id
        return f"OVERCHARGED ({results['overcharged']} lines)", job.id
    
    if results['unexpected'] > 0:
        return f"UNEXPECTED COSTS ({results['unexpected']} lines)", job.id
        
    return f"PARTIAL AUDIT ({results['matched']}/{results['total_lines']})", job.id
