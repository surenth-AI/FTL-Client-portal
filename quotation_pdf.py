"""
ReportLab-based PDF Quotation Generator for Fast Transit Line (FTL).
Replicates the exact client layout, coordinates, fonts, and styling of Quote FTL.pdf.
"""

import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Page size: US Letter (612 x 792 pt)
PAGE_WIDTH, PAGE_HEIGHT = letter

# Register Windows TrueType fonts with fallbacks
_FONTS_REGISTERED = False

def register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    font_mappings = [
        ('Arial', r'C:\Windows\Fonts\arial.ttf', 'Helvetica'),
        ('Arial-Bold', r'C:\Windows\Fonts\arialbd.ttf', 'Helvetica-Bold'),
        ('Tahoma', r'C:\Windows\Fonts\tahoma.ttf', 'Helvetica'),
        ('Tahoma-Bold', r'C:\Windows\Fonts\tahomabd.ttf', 'Helvetica-Bold'),
        ('TimesNewRoman', r'C:\Windows\Fonts\times.ttf', 'Times-Roman'),
        ('TimesNewRoman-Bold', r'C:\Windows\Fonts\timesbd.ttf', 'Times-Bold'),
    ]

    for name, path, fallback in font_mappings:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:
                pass

    _FONTS_REGISTERED = True

def get_font_name(preferred, fallback='Helvetica'):
    try:
        pdfmetrics.getFont(preferred)
        return preferred
    except KeyError:
        return fallback

def y_pt(y_from_top):
    """Convert top-down y coordinate (from PyMuPDF/client layout) to ReportLab bottom-up y."""
    return PAGE_HEIGHT - y_from_top

def fmt_num(val, decimals=2):
    if val is None or val == '':
        return ''
    try:
        f = float(val)
    except (ValueError, TypeError):
        return str(val)
    return f"{f:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def draw_caps_bold_words(c, x, y_top, words_str, font_bold='Tahoma-Bold', font_reg='Tahoma', font_size=8.5):
    """Draw string where each word's initial capital is bold and rest is regular."""
    cur_x = x
    words = words_str.split(' ')
    for i, w in enumerate(words):
        if not w:
            continue
        first_char = w[0]
        rest = w[1:]
        
        # Draw initial char in bold
        c.setFont(font_bold, font_size)
        c.drawString(cur_x, y_pt(y_top), first_char)
        cur_x += c.stringWidth(first_char, font_bold, font_size)
        
        # Draw rest in regular
        if rest:
            c.setFont(font_reg, font_size)
            c.drawString(cur_x, y_pt(y_top), rest)
            cur_x += c.stringWidth(rest, font_reg, font_size)
            
        if i < len(words) - 1:
            c.setFont(font_reg, font_size)
            c.drawString(cur_x, y_pt(y_top), ' ')
            cur_x += c.stringWidth(' ', font_reg, font_size)

def draw_clipped_text(c, x, y_top, text, max_x=215.3, font_name='Arial', font_size=7.5):
    """Draw text clipped strictly at max_x, cutting partway through a character if necessary."""
    c.setFont(font_name, font_size)
    text_w = c.stringWidth(text, font_name, font_size)
    if x + text_w > max_x:
        c.saveState()
        p = c.beginPath()
        p.rect(x - 1, y_pt(y_top + 4), max_x - (x - 1), 16)
        c.clipPath(p, stroke=0, fill=0)
        c.drawString(x, y_pt(y_top), text)
        c.restoreState()
    else:
        c.drawString(x, y_pt(y_top), text)

def generate_quotation_pdf(data):
    """
    Generate a 2-page quotation PDF with exact client positioning.
    """
    register_fonts()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    fn_arial = get_font_name('Arial', 'Helvetica')
    fn_arial_bd = get_font_name('Arial-Bold', 'Helvetica-Bold')
    fn_tahoma = get_font_name('Tahoma', 'Helvetica')
    fn_tahoma_bd = get_font_name('Tahoma-Bold', 'Helvetica-Bold')
    fn_times = get_font_name('TimesNewRoman', 'Times-Roman')
    fn_times_bd = get_font_name('TimesNewRoman-Bold', 'Times-Bold')

    # Colors
    col_blue = HexColor('#0469B5')
    col_grey_bar = HexColor('#E2E2E2')
    col_haz_bar = HexColor('#E0E0E0')
    col_light_blue = HexColor('#F0F8FF')
    col_sailing_grey = HexColor('#EBEBEB')
    col_company_grey = HexColor('#5F5F5F')

    quote_number = str(data.get('quote_number') or '')
    print_date = str(data.get('print_date') or '')
    to_company = str(data.get('to_company') or '')
    attn_name = str(data.get('attn_name') or '')
    from_name = str(data.get('from_name') or '')
    from_email = str(data.get('from_email') or '')
    from_phone = str(data.get('from_phone') or '')
    logo_path = data.get('logo_path')

    inco_term = str(data.get('inco_term') or 'CFR').strip().upper()
    por_loc = str(data.get('por_location') or '')
    pol_loc = str(data.get('pol_location') or '')
    pod_loc = str(data.get('pod_location') or '')
    del_loc = str(data.get('del_location') or pod_loc)

    total_packages = data.get('total_packages') or 1
    total_weight = float(data.get('total_weight') or 0.0)
    total_volume = float(data.get('total_volume') or 0.0)

    commodities = data.get('commodities') or []
    first_comm = commodities[0] if commodities else {}
    comm_pkg = f"{first_comm.get('nrPackages', total_packages)} {first_comm.get('packageCode', 'BX')}".strip()
    comm_desc = str(first_comm.get('commodityDescription') or first_comm.get('description') or 'General Cargo')
    comm_weight = float(first_comm.get('weight') or total_weight)
    comm_vol = float(first_comm.get('volume') or total_volume)
    comm_dims = first_comm.get('dimensions') or {}

    haz_un = str(data.get('haz_un') or '')
    haz_class = str(data.get('haz_class') or '')
    haz_pg = str(data.get('haz_pg') or '')

    currency_groups = data.get('currency_groups') or []
    quotation_currency = str(data.get('quotation_currency') or 'USD').strip().upper()
    grand_total = float(data.get('grand_total') or 0.0)
    roe_text = str(data.get('roe_text') or 'EUR = 1, USD = 2,00')

    valid_from = str(data.get('valid_from_formatted') or '')
    valid_until = str(data.get('valid_until_formatted') or '')
    pickup_remarks = str(data.get('pickup_remarks') or 'Please note that the free time for pick up is limited to 30 Minutes.')
    destination_clean = str(data.get('destination_clean') or pod_loc or 'Singapore')

    # =========================================================================
    # PAGE 1
    # =========================================================================

    # 1. Header Box: (51.0, 21.36) to (561.36, 116.64) - Height: 95.28 pt
    c.setLineWidth(0.96)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0, 0, 0)
    c.rect(51.00, y_pt(116.64), 561.36 - 51.00, 116.64 - 21.36, fill=0, stroke=1)

    # Vertical divider inside header at x = 305.88 (from 21.48 to 116.64)
    c.line(305.88, y_pt(21.48), 305.88, y_pt(116.64))

    # Divider line under Attn. at y = 69.48 (from 51.36 to 307.08)
    c.setLineWidth(0.84)
    c.line(51.36, y_pt(69.48), 307.08, y_pt(69.48))
    c.setLineWidth(0.96)

    # Header Left: Labels (Arial-Bold 7.5pt at x = 56.4)
    c.setFont(fn_arial_bd, 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(56.4, y_pt(31.6), 'Quotation No.:')
    c.drawString(56.4, y_pt(42.2), 'Print Date:')
    c.drawString(56.4, y_pt(53.0), 'To:')
    c.drawString(56.4, y_pt(64.3), 'Attn.:')
    c.drawString(56.4, y_pt(82.6), 'From:')
    c.drawString(56.4, y_pt(96.1), 'Email:')
    c.drawString(56.4, y_pt(110.2), 'Phone:')

    # Header Left: Values (Arial 8.5pt at x = 139.9)
    c.setFont(fn_arial, 8.5)
    c.drawString(139.9, y_pt(32.5), quote_number)
    c.drawString(139.9, y_pt(43.4), print_date)
    c.drawString(139.9, y_pt(54.4), to_company)
    c.drawString(139.9, y_pt(66.2), attn_name)
    c.drawString(139.9, y_pt(82.6), from_name)
    c.drawString(139.9, y_pt(96.1), from_email)
    c.drawString(139.9, y_pt(110.2), from_phone)

    # Header Right: Logo at x=322.32, y=36.72 to 100.80 (width=102.36, height=64.08)
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 322.32, y_pt(100.80), width=102.36, height=64.08, mask='auto')
        except Exception:
            pass

    # Header Right: Company Address at x = 432.2 (Arial 7.5pt, #5F5F5F, lines 8.7pt apart starting at baseline 54.1)
    # Ensure full 5-line company block:
    # 1. Company Name
    # 2. Address line 1
    # 3. Zip + City
    # 4. Country
    # 5. PHONE
    c.setFont(fn_arial, 7.5)
    c.setFillColor(col_company_grey)
    raw_addr_lines = data.get('company_address_lines') or []
    comp_name = data.get('company_name') or 'FAST TRANSIT LINE'
    comp_phone = data.get('company_phone') or '+32 (0)3 5419676'
    phone_str = comp_phone if comp_phone.upper().startswith('PHONE:') else f"PHONE: {comp_phone}"

    address_lines = []
    # If raw_addr_lines already has 5 lines and starts with company name, use it
    if len(raw_addr_lines) >= 5 and raw_addr_lines[0].upper() == comp_name.upper():
        address_lines = raw_addr_lines[:5]
    else:
        address_lines.append(comp_name)
        for al in raw_addr_lines:
            if al.upper() != comp_name.upper() and not al.upper().startswith('PHONE:'):
                address_lines.append(al)
        if len(address_lines) == 1:
            address_lines.extend(['SCHOUWKENSSTRAAT 1', '2030 ANTWERPEN', 'BELGIUM'])
        address_lines.append(phone_str)

    cur_y = 54.1
    for line in address_lines[:5]:
        c.drawString(432.2, y_pt(cur_y), line)
        cur_y += 8.7

    # 2. QUOTATION Title Bar & Blue Lines
    # Client has two separate 3.2pt blue lines with white gaps around the black bar:
    # Top blue line: y = 123.6 to 126.8 (3.2pt)
    c.setFillColor(col_blue)
    c.rect(53.04, y_pt(126.80), 561.60 - 53.04, 126.80 - 123.60, fill=1, stroke=0)

    # Black bar: y = 129.24 to 142.80 (13.56pt tall), separated by 2.44pt white gap above
    c.setFillColorRGB(0, 0, 0)
    c.rect(53.04, y_pt(142.80), 561.60 - 53.04, 142.80 - 129.24, fill=1, stroke=0)

    # Quotation title text: Arial-Bold 12.2pt, White, centered horizontally
    c.setFont(fn_arial_bd, 12.2)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString((53.04 + 561.60) / 2.0, y_pt(140.4), '*** QUOTATION ***')

    # Bottom blue line: y = 145.00 to 148.32 (3.32pt), separated by 2.20pt white gap below black bar
    c.setFillColor(col_blue)
    c.rect(53.04, y_pt(148.32), 561.60 - 53.04, 148.32 - 145.00, fill=1, stroke=0)

    # 3. Main Body Box: Starts at y = 159.00 (11pt gap below bar) to 746.16
    c.setLineWidth(0.96)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(51.36, y_pt(746.16), 561.36 - 51.36, 746.16 - 159.00, fill=0, stroke=1)

    # 4. Greeting ("Dear ..."): Inset at x = 60.5, Tahoma 7.5pt
    c.setFont(fn_tahoma, 7.5)
    c.setFillColorRGB(0, 0, 0)
    greeting_contact = f"Dear {attn_name}, " if attn_name else "Dear , "
    c.drawString(60.5, y_pt(171.6), greeting_contact)
    c.drawString(60.5, y_pt(180.7), 'we thank you for your request. Please find herewith our rate and tentative sailing schedule. With future correspondence in regard to this rate offer, ')
    c.drawString(60.5, y_pt(190.0), 'please refer to above mentioned quotation ID nr. If you have any further questions, please do not hesitate to contact us.')

    # 5. Section: ROUTING & INCO TERM
    # Heavy line above ROUTING: y = 203.88 (from 51.36 to 562.08)
    c.line(51.36, y_pt(203.88), 562.08, y_pt(203.88))

    # Split grey bar: ROUTING (51.84 to 465.00) and INCO TERM (466.08 to 559.44), y = 204.60 to 215.88 (NO outline)
    c.setFillColor(col_grey_bar)
    c.rect(51.84, y_pt(215.88), 465.00 - 51.84, 215.88 - 204.60, fill=1, stroke=0)
    c.rect(466.08, y_pt(215.88), 559.44 - 466.08, 215.88 - 204.60, fill=1, stroke=0)

    # Bar titles: Arial-Bold 9.3pt, black, baseline 213.2
    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(51.8, y_pt(213.2), ' ROUTING')
    c.drawString(466.1, y_pt(213.2), f' INCO TERM: {inco_term}')

    # Routing rows: Labels Arial-Bold 8.5pt at x = 59.0; Values Arial 9.3pt at x = 161.4
    c.setFont(fn_arial_bd, 8.5)
    c.drawString(59.0, y_pt(225.6), 'PLACE OF RECEIPT:')
    c.drawString(59.0, y_pt(237.4), 'PORT OF LOADING:')
    c.drawString(59.0, y_pt(248.8), 'PORT OF DISCHARGE:')

    c.setFont(fn_arial, 9.3)
    c.drawString(161.4, y_pt(226.1), por_loc)
    c.drawString(161.4, y_pt(237.8), pol_loc)
    c.drawString(161.4, y_pt(249.4), pod_loc)

    # FINAL DESTINATION: Label at x = 314.6; Value at x = 408.1
    c.setFont(fn_arial_bd, 8.5)
    c.drawString(314.6, y_pt(248.6), 'FINAL DESTINATION:')
    c.setFont(fn_arial, 9.3)
    c.drawString(408.1, y_pt(249.0), del_loc)

    # 6. Section: CARGO DETAILS
    # Heavy line above: y = 253.92
    c.line(51.36, y_pt(253.92), 562.08, y_pt(253.92))

    # Grey bar: (52.44 to 561.12), y = 255.60 to 266.88 (NO outline)
    c.setFillColor(col_grey_bar)
    c.rect(52.44, y_pt(266.88), 561.12 - 52.44, 266.88 - 255.60, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(52.4, y_pt(264.2), ' CARGO DETAILS')

    # Cargo headers: Arial-Bold 7.5pt, baseline 277.8
    c.setFont(fn_arial_bd, 7.5)
    c.drawString(57.5, y_pt(277.8), 'No. and kind of packages')
    c.drawString(167.3, y_pt(277.8), 'Description')
    c.drawString(429.8, y_pt(277.8), 'Weight (kgs)')
    c.drawString(494.9, y_pt(277.8), 'Volume (m³)')

    # Line under headers: y = 282.24 (width 0.84)
    c.setLineWidth(0.84)
    c.line(57.60, y_pt(282.24), 558.72, y_pt(282.24))
    c.setLineWidth(0.96)

    # Cargo values: Arial 9.3pt, baseline 293.2
    c.setFont(fn_arial, 9.3)
    c.drawString(57.5, y_pt(291.7), comm_pkg)
    c.drawString(167.4, y_pt(293.2), comm_desc)
    c.drawRightString(486.7, y_pt(293.2), fmt_num(comm_weight, 2))
    c.drawRightString(551.8, y_pt(293.2), fmt_num(comm_vol, 2))

    # Full-width line below the cargo row: y = 300.24
    c.line(56.40, y_pt(300.24), 557.64, y_pt(300.24))

    # Dimensions Section:
    # Label at baseline 313.2, Arial 9.3pt
    c.drawString(58.1, y_pt(313.2), 'Dimensions')

    # Very fine outline (0.2pt line, dash [2.1, 0.25] 0)
    c.saveState()
    c.setLineWidth(0.2)
    c.setStrokeColorRGB(0, 0, 0)
    c.setDash([2.1, 0.25], 0)
    c.rect(167.5, y_pt(329.6), 335.0 - 167.5, 329.6 - 305.3, fill=0, stroke=1)
    c.restoreState()

    # Dotted box headers: Arial regular 8.5pt at x = 198.5, 240.2, 268.1, 302.4, baseline 313.4
    c.setFont(fn_arial, 8.5)
    c.drawString(198.5, y_pt(313.4), '#')
    c.drawString(240.2, y_pt(313.4), 'L')
    c.drawString(268.1, y_pt(313.4), 'W')
    c.drawString(302.4, y_pt(313.4), 'H')

    # Line under headers in Dimensions box: Dotted in client! (width 0.375, dash [0.375, 0.375] 0)
    c.saveState()
    c.setLineWidth(0.375)
    c.setDash([0.375, 0.375], 0)
    c.line(168.00, y_pt(317.16), 335.04, y_pt(317.16))
    c.restoreState()

    # Dimensions values if present
    if isinstance(comm_dims, dict) and (comm_dims.get('amount') or comm_dims.get('length')):
        c.setFont(fn_arial, 8.5)
        c.drawString(198.5, y_pt(325.5), str(comm_dims.get('amount') or '1'))
        c.drawString(240.2, y_pt(325.5), str(comm_dims.get('length') or '0'))
        c.drawString(268.1, y_pt(325.5), str(comm_dims.get('width') or '0'))
        c.drawString(302.4, y_pt(325.5), str(comm_dims.get('height') or '0'))

    # Line below dimensions: y = 346.20
    c.line(57.00, y_pt(346.20), 558.12, y_pt(346.20))

    # Totals row: Labels at x = 58.7, 167.5, 325.1 (Arial-Bold 8.5pt, baseline 359.0)
    c.setFont(fn_arial_bd, 8.5)
    c.drawString(58.7, y_pt(359.0), 'TOTAL #:')
    c.drawString(167.5, y_pt(359.0), 'TOTAL WEIGHT:')
    c.drawString(325.1, y_pt(359.0), 'TOTAL VOLUME:')

    # Totals values: Fixed positions at x = 104.6, 244.1, 404.9 (Arial 9.3pt, baseline 359.6)
    c.setFont(fn_arial, 9.3)
    c.drawString(104.6, y_pt(359.6), str(total_packages))
    c.drawString(244.1, y_pt(359.6), fmt_num(total_weight, 2))
    c.drawString(404.9, y_pt(359.6), fmt_num(total_volume, 2))

    # 7. Section: HAZARDOUS INFORMATION
    # Heavy line above: y = 364.80
    c.line(51.12, y_pt(364.80), 561.96, y_pt(364.80))

    # Grey bar: (52.56 to 559.92), y = 367.08 to 376.20, fill #E0E0E0 (NO outline)
    c.setFillColor(col_haz_bar)
    c.rect(52.56, y_pt(376.20), 559.92 - 52.56, 376.20 - 367.08, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(54.1, y_pt(374.4), 'HAZARDOUS INFORMATION:')

    # Haz values: Arial 7.5pt, baseline 387.5 at x = 60.2, 114.6, 195.7
    c.setFont(fn_arial, 7.5)
    c.drawString(60.2, y_pt(387.5), f'UN: {haz_un}'.strip())
    c.drawString(114.6, y_pt(387.5), f'CLASS: {haz_class}'.strip())
    c.drawString(195.7, y_pt(387.5), f'PG: {haz_pg}'.strip())

    # 8. Section: TARIFF
    # Heavy line above: y = 397.44
    c.line(50.76, y_pt(397.44), 561.60, y_pt(397.44))

    # Grey bar: (52.44 to 560.88), y = 398.64 to 409.92 (NO outline)
    c.setFillColor(col_grey_bar)
    c.rect(52.44, y_pt(409.92), 560.88 - 52.44, 409.92 - 398.64, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(52.4, y_pt(407.3), 'TARIFF')

    # Light-blue panel: Inset at x = 60.0 to 549.84, y = 416.76 to 605.16 (ends 2.4pt above Total Overall)
    c.setFillColor(col_light_blue)
    c.rect(60.00, y_pt(605.16), 549.84 - 60.00, 605.16 - 416.76, fill=1, stroke=0)

    # Tariff Header Row: 17.3pt below bar -> baseline 427.2, Arial-Bold 7.5pt
    c.setFont(fn_arial_bd, 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(62.8, y_pt(427.2), 'Description')
    c.drawRightString(257.5, y_pt(427.2), 'Price')
    c.drawRightString(301.3, y_pt(427.2), 'Minimum')
    c.drawRightString(359.1, y_pt(427.2), 'Qty')
    c.drawString(367.9, y_pt(427.2), 'CalcCode')
    c.drawString(439.2, y_pt(427.2), 'Curr.')
    c.drawRightString(521.1, y_pt(427.2), 'Total')

    # Header underline: solid 0.38pt line at y = 432.24
    c.setLineWidth(0.38)
    c.line(62.76, y_pt(432.24), 524.88, y_pt(432.24))

    # Tariff Data Rows: First row at 453.0 (20.8pt below header line), 11.3pt spacing
    cur_tariff_y = 453.0

    for g_idx, grp in enumerate(currency_groups):
        lines = grp.get('lines') or []
        curr = grp.get('currency', 'EUR')
        subtotal = float(grp.get('subtotal') or 0.0)
        converted_amt = grp.get('converted_amount')

        for l in lines:
            aname = str(l.get('articleName') or '').strip()
            price_val = float(l.get('price') or 0.0)
            min_val = l.get('minimum')
            qty_val = float(l.get('qty') or 1.0)
            calc_code = str(l.get('calcCode') or 'LUMPSUM').strip()
            amt_val = float(l.get('amount') or 0.0)

            # Draw description clipped partway through letter at exactly x = 215.3
            draw_clipped_text(c, 62.8, cur_tariff_y, aname, max_x=215.3, font_name=fn_arial, font_size=7.5)

            c.setFont(fn_arial, 7.5)
            c.drawRightString(257.5, y_pt(cur_tariff_y), fmt_num(price_val, 2))

            if min_val is not None and min_val != '':
                c.drawRightString(301.3, y_pt(cur_tariff_y), fmt_num(min_val, 2))

            c.drawRightString(359.1, y_pt(cur_tariff_y), fmt_num(qty_val, 3))
            c.drawString(367.9, y_pt(cur_tariff_y), calc_code)
            c.drawString(439.2, y_pt(cur_tariff_y), curr)
            c.drawRightString(521.1, y_pt(cur_tariff_y), fmt_num(amt_val, 2))

            cur_tariff_y += 11.3

        # Subtotal line: Dotted in client! (width 0.375, dash [0.375, 0.375] 0, from 65.64 to 524.16)
        sub_line_y = cur_tariff_y - 11.3 + 5.4
        c.saveState()
        c.setLineWidth(0.375)
        c.setDash([0.375, 0.375], 0)
        c.line(65.64, y_pt(sub_line_y), 524.16, y_pt(sub_line_y))
        c.restoreState()

        # Subtotal row: baseline = sub_line_y + 7.5
        sub_text_y = sub_line_y + 7.5
        c.setFont(fn_arial_bd, 7.5)
        c.drawString(439.2, y_pt(sub_text_y), curr)
        c.drawRightString(521.1, y_pt(sub_text_y), fmt_num(subtotal, 2))

        # Currency conversion line if applicable
        if converted_amt is not None and g_idx < len(currency_groups) - 1:
            conv_y = sub_text_y + 15.8
            c.drawString(427.9, y_pt(conv_y), '=')
            c.drawString(439.2, y_pt(conv_y), quotation_currency)
            c.drawRightString(521.1, y_pt(conv_y), fmt_num(converted_amt, 2))
            cur_tariff_y = conv_y + 24.3
        else:
            cur_tariff_y = sub_text_y + 11.3

    # Grand Total Line: Solid line stays solid at y = 582.60
    c.setLineWidth(0.38)
    c.line(62.04, y_pt(582.60), 524.16, y_pt(582.60))

    # Grand Total Row: 14pt below line -> baseline 596.9, Arial-Bold 9.3pt
    c.setFont(fn_arial_bd, 9.3)
    c.drawString(439.2, y_pt(596.9), quotation_currency)
    c.drawRightString(520.8, y_pt(596.9), fmt_num(grand_total, 2))

    # 9. Section: TOTAL OVERALL
    # Single heavy line above: y = 607.56 (NO outlines on grey bar)
    c.setLineWidth(0.96)
    c.line(51.00, y_pt(607.56), 561.72, y_pt(607.56))

    # Grey bar: (52.44 to 561.12), y = 607.92 to 619.20 (NO outline)
    c.setFillColor(col_grey_bar)
    c.rect(52.44, y_pt(619.20), 561.12 - 52.44, 619.20 - 607.92, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(52.4, y_pt(616.7), 'TOTAL OVERALL')

    # Exchange rate notice text: Tahoma 8.5pt at x = 61.3, full width (breaks after "differ at ")
    c.setFont(fn_tahoma, 8.5)
    c.drawString(61.3, y_pt(632.5), 'The applied rate of exchange (R.O.E.) is an estimate and subject to change without advance notice, the total amount might differ at ')
    c.drawString(61.3, y_pt(642.7), f'the time. {roe_text}')

    # 10. Section: REMARKS (Validity) - NO line above!
    c.setFillColor(col_grey_bar)
    c.rect(52.08, y_pt(658.56), 560.64 - 52.08, 658.56 - 647.28, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(52.1, y_pt(655.9), 'REMARKS')

    # Body line 1: validity dates with bold dates
    c.setFont(fn_tahoma, 8.5)
    c.drawString(61.3, y_pt(667.7), 'The OceanFreight has a validity from ')
    w1 = c.stringWidth('The OceanFreight has a validity from ', fn_tahoma, 8.5)

    c.setFont(fn_tahoma_bd, 8.5)
    c.drawString(61.3 + w1, y_pt(667.7), f'{valid_from} ')
    w2 = c.stringWidth(f'{valid_from} ', fn_tahoma_bd, 8.5)

    c.setFont(fn_tahoma, 8.5)
    c.drawString(61.3 + w1 + w2, y_pt(667.7), 'up and until ')
    w3 = c.stringWidth('up and until ', fn_tahoma, 8.5)

    c.setFont(fn_tahoma_bd, 8.5)
    c.drawString(61.3 + w1 + w2 + w3, y_pt(667.7), valid_until)

    # Body line 2: Surcharges + Fuel are Valid At Time Of Shipment (with bold capital initials)
    c.setFont(fn_tahoma, 8.5)
    c.drawString(61.3, y_pt(677.9), 'Surcharges + Fuel are ')
    w_prefix = c.stringWidth('Surcharges + Fuel are ', fn_tahoma, 8.5)
    draw_caps_bold_words(c, 61.3 + w_prefix, 677.9, 'Valid At Time Of Shipment', fn_tahoma_bd, fn_tahoma, 8.5)

    # 11. Section: PICK UP - NO line above!
    c.setFillColor(col_grey_bar)
    c.rect(53.04, y_pt(697.32), 561.60 - 53.04, 697.32 - 686.04, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(53.0, y_pt(694.7), 'PICK UP')

    c.setFont(fn_tahoma, 8.5)
    c.drawString(61.3, y_pt(707.5), pickup_remarks)

    # 12. Section: REMARKS (General) - NO line above!
    c.setFillColor(col_grey_bar)
    c.rect(52.44, y_pt(723.00), 561.12 - 52.44, 723.00 - 711.72, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(52.4, y_pt(720.5), 'REMARKS')

    # Page 1 Footer: baseline 767.2 (Quotation ID bold 7.5pt, ID regular 8.5pt, Pagina 1 van 2 at 558.7)
    c.setFont(fn_arial_bd, 7.5)
    c.drawString(50.2, y_pt(767.2), 'Quotation ID:')
    c.setFont(fn_arial, 8.5)
    c.drawString(100.9, y_pt(767.9), quote_number)

    c.setFont(fn_arial, 9.3)
    c.drawRightString(558.7, y_pt(768.7), 'Pagina 1 van 2')

    c.showPage()

    # =========================================================================
    # PAGE 2
    # =========================================================================

    # Page 2 Border Box: (51.12, 17.40) to (561.60, 186.84) - Leaves 20pt of space below sailing table!
    c.setLineWidth(0.96)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(51.12, y_pt(186.84), 561.60 - 51.12, 186.84 - 17.40, fill=0, stroke=1)

    # 1. Section: REMARKS FOR {Destination} - 3pt gap below top border (starts at y = 20.40)
    c.setFillColor(col_grey_bar)
    c.rect(52.44, y_pt(31.68), 561.12 - 52.44, 31.68 - 20.40, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(52.4, y_pt(29.0), f'REMARKS FOR {destination_clean}')

    # 15pt empty space below bar before TERMS AND CONDITIONS (starts at 47.28)
    # 2. Section: TERMS AND CONDITIONS
    c.setFillColor(col_grey_bar)
    c.rect(53.04, y_pt(58.56), 561.60 - 53.04, 58.56 - 47.28, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(53.0, y_pt(55.9), 'TERMS AND CONDITIONS')

    # Terms & Conditions Body: Times New Roman 8.5pt at x = 61.3, line spacing 10pt
    c.setFont(fn_times, 8.5)
    tc_lines = [
        'Quotation valid for standard, harmless cargo.',
        'DAP CHARGES: Offers based on commercial deliveries.',
        'In case of personal effects/domestic delivery please contact us',
        'Long lenght surcharge applicable as from 5m90.',
        'High cube surcharge applicable as from 2m25.'
    ]
    cur_tc_y = 67.7
    for tcl in tc_lines:
        c.drawString(61.3, y_pt(cur_tc_y), tcl)
        cur_tc_y += 9.9

    # 3. Single 1pt line above SAILING SCHEDULE: y = 113.52
    c.setLineWidth(0.96)
    c.line(51.36, y_pt(113.52), 562.08, y_pt(113.52))

    # 4. Section: SAILING SCHEDULE FOR {Destination}
    c.setFillColor(col_grey_bar)
    c.rect(51.36, y_pt(126.72), 559.92 - 51.36, 126.72 - 115.44, fill=1, stroke=0)

    c.setFont(fn_arial_bd, 9.3)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(51.4, y_pt(124.1), f'SAILING SCHEDULE FOR {destination_clean}')

    # 5. Sailing Schedule Table: Inset at x = 69.12 to 526.92, y = 133.08 to 166.80
    c.rect(69.12, y_pt(166.80), 526.92 - 69.12, 166.80 - 133.08, fill=0, stroke=1)

    # Column dividers at exact positions:
    # 195.36 (Vessel), 235.56 (Voyage), 274.32 (POL), 331.56 (Closing), 395.76 (ETD), 454.92 (ETA)
    dividers = [195.36, 235.56, 274.32, 331.56, 395.76, 454.92]
    for div_x in dividers:
        c.line(div_x, y_pt(133.08), div_x, y_pt(166.80))

    # Sailing table headers: Arial-Bold 8.5pt, left-aligned at exact x coordinates, baseline 141.2
    c.setFont(fn_arial_bd, 8.5)
    c.drawString(73.2, y_pt(141.2), 'Vessel')
    c.drawString(199.1, y_pt(141.2), 'Voyage')
    c.drawString(238.3, y_pt(141.2), 'POL')
    c.drawString(280.5, y_pt(141.2), 'Closing')
    c.drawString(339.1, y_pt(141.2), 'ETD')
    c.drawString(401.2, y_pt(141.2), 'ETA')
    c.drawString(459.1, y_pt(141.5), 'DESTINATION')

    # Line under headers: y = 145.80 (width 0.84)
    c.setLineWidth(0.84)
    c.line(68.40, y_pt(145.80), 526.92, y_pt(145.80))
    c.setLineWidth(0.96)

    # First data row: shaded grey (#EBEBEB), inset by ~2pt (70.92 to 525.48, y = 148.56 to 157.56)
    c.setFillColor(col_sailing_grey)
    c.rect(70.92, y_pt(157.56), 525.48 - 70.92, 157.56 - 148.56, fill=1, stroke=0)

    # Horizontal divider between row 1 and row 2: y = 158.40
    c.line(69.12, y_pt(158.40), 527.64, y_pt(158.40))

    # Sailing data if available
    sailings = data.get('sailings') or []
    if sailings:
        c.setFont(fn_arial, 7.5)
        c.setFillColorRGB(0, 0, 0)
        row_ys = [154.0, 163.5]
        for s_idx, s in enumerate(sailings[:2]):
            s_y = row_ys[s_idx]
            c.drawString(73.2, y_pt(s_y), str(s.get('vessel') or s.get('vesselName') or ''))
            c.drawString(199.1, y_pt(s_y), str(s.get('voyage') or s.get('voyageNo') or ''))
            c.drawString(238.3, y_pt(s_y), str(s.get('pol') or pol_loc or ''))
            c.drawString(280.5, y_pt(s_y), str(s.get('closing') or ''))
            c.drawString(339.1, y_pt(s_y), str(s.get('etd') or ''))
            c.drawString(401.2, y_pt(s_y), str(s.get('eta') or ''))
            c.drawString(459.1, y_pt(s_y), str(s.get('pod') or destination_clean or ''))

    # Page 2 Footer: baseline 767.2
    c.setFont(fn_arial_bd, 7.5)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(50.2, y_pt(767.2), 'Quotation ID:')
    c.setFont(fn_arial, 8.5)
    c.drawString(100.9, y_pt(767.9), quote_number)

    c.setFont(fn_arial, 9.3)
    c.drawRightString(558.7, y_pt(768.7), 'Pagina 2 van 2')

    c.showPage()
    c.save()

    return buffer.getvalue()
