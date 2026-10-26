import tempfile
import os
import sys
import json
import fitz
from io import BytesIO

sys.stdout.reconfigure(encoding='utf-8')

# Patch xhtml2pdf temporary file locking on Windows
import xhtml2pdf.files as xf

def monkey_get_named_tmp_file(self):
    data = self.get_data()
    if hasattr(self, 'path') and self.path and os.path.isfile(str(self.path)):
        class DummyFile:
            def __init__(self, name):
                self.name = name
        return DummyFile(str(self.path))
    fd, path = tempfile.mkstemp(suffix=self.suffix or '.ttf')
    if data:
        os.write(fd, data)
    os.close(fd)
    class TempHolder:
        def __init__(self, name):
            self.name = name
    return TempHolder(path)

xf.BaseFile.get_named_tmp_file = monkey_get_named_tmp_file

from xhtml2pdf import pisa
from jinja2 import Environment

def link_callback(uri, rel):
    if uri.startswith('font:'):
        font_name = uri.split(':', 1)[1]
        font_map = {
            'arial': r'C:\Windows\Fonts\arial.ttf',
            'arial-bold': r'C:\Windows\Fonts\arialbd.ttf',
            'tahoma': r'C:\Windows\Fonts\tahoma.ttf',
            'tahoma-bold': r'C:\Windows\Fonts\tahomabd.ttf',
            'times': r'C:\Windows\Fonts\times.ttf',
        }
        return font_map.get(font_name.lower(), uri)
    return uri

# Helper formatting functions
def fmt_num(val, decimals=2):
    if val is None or val == '':
        return ''
    try:
        f = float(val)
    except (ValueError, TypeError):
        return str(val)
    formatted = f"{f:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return formatted

def fmt_date(val, leading_zero=True):
    if not val:
        return ''
    val_str = str(val).strip()
    import re
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', val_str)
    if m:
        y, m, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if leading_zero:
            return f"{d:02d}/{m:02d}/{y}"
        else:
            return f"{d}/{m}/{y}"
    m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})', val_str)
    if m:
        d, m, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if leading_zero:
            return f"{d:02d}/{m:02d}/{y}"
        else:
            return f"{d}/{m}/{y}"
    if hasattr(val, 'day'):
        if leading_zero:
            return f"{val.day:02d}/{val.month:02d}/{val.year}"
        else:
            return f"{val.day}/{val.month}/{val.year}"
    return val_str

def clean_location(loc):
    if not loc:
        return ''
    s = str(loc).strip()
    if ' - ' in s:
        s = s.split(' - ')[0].strip()
    if '(' in s:
        s = s.split('(')[0].strip()
    return s.title()

def truncate_str(s, max_len=33):
    if not s:
        return ''
    st = str(s).strip()
    if len(st) > max_len:
        return st[:max_len]
    return st

# Test with last_api_response_2.json
with open(os.path.join(tempfile.gettempdir(), 'last_api_response_2.json'), encoding='utf-8') as f:
    api_resp = json.load(f)

q_data = api_resp.get('quotation', api_resp)
header = q_data.get('header', {})
commodities = q_data.get('commodities', [])
sailings = q_data.get('sailings', [])
tariff = q_data.get('tariff', q_data)
breakdown = tariff.get('lines', []) if isinstance(tariff, dict) else []

quotation_currency = (tariff.get('quotationCurrency') if isinstance(tariff, dict) else None) or header.get('currency') or 'USD'
quotation_currency = quotation_currency.strip().upper()

# Exchange rate
exchange_rate_val = None
from_curr = quotation_currency or 'EUR'
to_curr = 'USD' if from_curr == 'EUR' else 'EUR'

if header.get('roe1') and float(header.get('roe1')) > 0:
    exchange_rate_val = float(header.get('roe1'))
    if header.get('cur1'): to_curr = header.get('cur1')
elif header.get('roe2') and float(header.get('roe2')) > 0:
    exchange_rate_val = float(header.get('roe2'))
    if header.get('cur2'): to_curr = header.get('cur2')

if not exchange_rate_val:
    for l in breakdown:
        r = float(l.get('exchangeRate') or 0.0)
        if r > 0 and r != 1.0:
            exchange_rate_val = r
            if l.get('currency') and l.get('currency') != from_curr:
                to_curr = l.get('currency')
            break

if not exchange_rate_val:
    exchange_rate_val = 2.0  # standard fallback when not returned

# Currency grouping
groups_map = {}
for item in breakdown:
    c = (item.get('currency') or quotation_currency).strip().upper()
    if c not in groups_map:
        groups_map[c] = []
    
    aname = (item.get('articleName') or '').strip()
    cg = (item.get('articleCostGroup') or '').strip().upper()
    calc = (item.get('calcCode') or item.get('calcCodeBase') or '').strip().upper()
    calc_code_display = 'W/M' if calc in ['MTQ', 'KGM', 'W/M'] else 'LUMPSUM'
    
    # Qty
    raw_qty = item.get('appliedQty')
    if raw_qty is not None and float(raw_qty) > 0:
        qty_val = float(raw_qty)
    else:
        # If commodities volume or weight is available
        vol = sum(float(c.get('volume') or 0) for c in commodities) if commodities else 0
        wt = sum(float(c.get('weight') or 0) for c in commodities) if commodities else 0
        chargeable = max(wt / 1000.0, vol)
        qty_val = chargeable if calc_code_display == 'W/M' and chargeable > 0 else 1.0
        
    rate_val = float(item.get('appliedRate') if item.get('appliedRate') is not None else (item.get('price') or item.get('amount') or 0.0))
    min_val = float(item.get('minimum')) if item.get('minimum') is not None else None
    amt_val = float(item.get('amount') or (rate_val * qty_val))
    
    groups_map[c].append({
        'articleName': aname,
        'articleCostGroup': cg,
        'price': rate_val,
        'minimum': min_val,
        'qty': qty_val,
        'calcCode': calc_code_display,
        'currency': c,
        'amount': amt_val
    })

# Order currency groups: non-quotation currencies first, quotation currency last
all_currs = list(groups_map.keys())
sorted_currs = [c for c in all_currs if c != quotation_currency] + ([quotation_currency] if quotation_currency in all_currs else [])

currency_groups = []
grand_total = 0.0

for c in sorted_currs:
    lines = groups_map[c]
    if c == quotation_currency:
        # Ocean freight lines first
        lines.sort(key=lambda l: 0 if ('OCEAN FREIGHT' in l['articleName'].upper() or 'FREIGHT' in l['articleName'].upper() or l['articleCostGroup'] == 'FC') else 1)
    
    subtotal = sum(l['amount'] for l in lines)
    converted_amount = None
    if c != quotation_currency and exchange_rate_val:
        converted_amount = round(subtotal * exchange_rate_val, 2)
        grand_total += converted_amount
    else:
        grand_total += subtotal
        
    currency_groups.append({
        'currency': c,
        'lines': lines,
        'subtotal': subtotal,
        'converted_amount': converted_amount
    })

print(f"Currency groups: {len(currency_groups)}")
for g in currency_groups:
    print(f"  Curr: {g['currency']}, lines: {len(g['lines'])}, subtotal: {g['subtotal']}, converted: {g['converted_amount']}")
print(f"Grand total: {grand_total}")
