from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from app.models.models import Rate, Booking, TrackingEvent, CargoItem, BookingAttachment, ShippingInstruction
from app.services.rate_engine import RateEngine
from app import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import json
import requests
import re

customer = Blueprint('customer', __name__)

def save_attachments(booking, files):
    """Utility to save multiple uploaded files to a booking."""
    if not files:
        return
    
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Add timestamp to avoid collisions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            
            attachment = BookingAttachment(
                booking_id=booking.id,
                filename=filename,
                file_path=save_path
            )
            db.session.add(attachment)

def process_cargo_items(booking, form, service_type):
    """Utility to process and save cargo items from form data."""
    if service_type == 'LCL':
        qty_list = form.getlist('item_qty[]')
        type_list = form.getlist('item_type[]')
        weight_list = form.getlist('item_weight[]')
        vol_list = form.getlist('item_volume[]')
        l_list = form.getlist('item_l[]')
        w_list = form.getlist('item_w[]')
        h_list = form.getlist('item_h[]')
        uom_list = form.getlist('item_uom[]')
        hs_list = form.getlist('item_hs[]')
        desc_list = form.getlist('item_desc[]')
        is_imo_list = form.getlist('item_is_imo[]')
        un_list = form.getlist('item_un[]')
        pg_list = form.getlist('item_pg[]')
        class_list = form.getlist('item_class[]')
        
        for i in range(len(qty_list)):
            item = CargoItem(
                booking_id=booking.id,
                quantity=int(qty_list[i]) if i < len(qty_list) and qty_list[i] else 0,
                package_type=type_list[i] if i < len(type_list) else '',
                weight_kg=float(weight_list[i]) if i < len(weight_list) and weight_list[i] else 0.0,
                volume_cbm=float(vol_list[i]) if i < len(vol_list) and vol_list[i] else 0.0,
                length=float(l_list[i]) if i < len(l_list) and l_list[i] else 0.0,
                width=float(w_list[i]) if i < len(w_list) and w_list[i] else 0.0,
                height=float(h_list[i]) if i < len(h_list) and h_list[i] else 0.0,
                uom=uom_list[i] if i < len(uom_list) else '',
                hs_code=hs_list[i] if i < len(hs_list) else '',
                description=desc_list[i] if i < len(desc_list) else None,
                is_imo=True if i < len(is_imo_list) and is_imo_list[i] == 'yes' else False,
                un_number=un_list[i] if i < len(un_list) else None,
                packing_group=pg_list[i] if i < len(pg_list) else None,
                imo_class=class_list[i] if i < len(class_list) else None
            )
            db.session.add(item)
    else: # FCL
        c_qty_list = form.getlist('cont_qty[]')
        c_type_list = form.getlist('cont_type[]')
        p_qty_list = form.getlist('cont_p_qty[]')
        p_type_list = form.getlist('cont_p_type[]')
        vol_list = form.getlist('cont_volume[]')
        weight_list = form.getlist('cont_weight[]')
        hs_list = form.getlist('cont_hs[]')
        desc_list = form.getlist('cont_desc[]')
        is_imo_list = form.getlist('cont_is_imo[]')
        un_list = form.getlist('cont_un[]')
        pg_list = form.getlist('cont_pg[]')
        class_list = form.getlist('cont_class[]')
        
        for i in range(len(c_qty_list)):
            item = CargoItem(
                booking_id=booking.id,
                container_count=int(c_qty_list[i]) if i < len(c_qty_list) and c_qty_list[i] else 0,
                container_type=c_type_list[i] if i < len(c_type_list) else '',
                quantity=int(p_qty_list[i]) if i < len(p_qty_list) and p_qty_list[i] else 0,
                package_type=p_type_list[i] if i < len(p_type_list) else '',
                volume_cbm=float(vol_list[i]) if i < len(vol_list) and vol_list[i] else 0.0,
                weight_kg=float(weight_list[i]) if i < len(weight_list) and weight_list[i] else 0.0,
                hs_code=hs_list[i] if i < len(hs_list) else '',
                description=desc_list[i] if i < len(desc_list) else None,
                is_imo=True if i < len(is_imo_list) and is_imo_list[i] == 'yes' else False,
                un_number=un_list[i] if i < len(un_list) else None,
                packing_group=pg_list[i] if i < len(pg_list) else None,
                imo_class=class_list[i] if i < len(class_list) else None
            )
            db.session.add(item)

def parse_location(loc_str):
    if not loc_str:
        return "", ""
    match = re.search(r'\((.*?)\)', loc_str)
    if match:
        return loc_str.replace(match.group(0), '').strip(), match.group(1).strip()
    return loc_str, ""

def post_booking_to_api(booking):
    try:
        por_name, por_code = parse_location(booking.place_of_receipt or booking.origin)
        pol_name, pol_code = parse_location(booking.origin)
        pod_name, pod_code = parse_location(booking.destination)
        del_name, del_code = parse_location(booking.place_of_delivery or booking.destination)
        
        is_hazmat = any(item.is_imo for item in booking.cargo_items)
        
        total_qty = sum([item.quantity for item in booking.cargo_items if item.quantity]) + sum([item.container_count for item in booking.cargo_items if item.container_count])
        total_weight = sum([item.weight_kg for item in booking.cargo_items if item.weight_kg])
        total_volume = sum([item.volume_cbm for item in booking.cargo_items if item.volume_cbm]) or booking.volume
        
        payload = [{
            "bookingID": 0, 
            "branchID": 1,
            "bookingRef": f"BK-{booking.id:06d}",
            "fileRef": f"FILE-{booking.id:06d}",
            "customerRef": booking.customer_ref or "N/A",
            "createdOn": booking.created_at.isoformat() + "Z" if booking.created_at else datetime.utcnow().isoformat() + "Z",
            "porLocode": por_code,
            "porLocation": por_name,
            "polLocode": pol_code,
            "polLocation": pol_name,
            "podLocode": pod_code,
            "podLocation": pod_name,
            "delLocode": del_code,
            "delLocation": del_name,
            "vessel": booking.vessel_name or "",
            "voyage": booking.voyage_number or "",
            "trafficType": booking.traffic_type or "EX",
            "isRoutingOrder": True,
            "isHazmat": is_hazmat,
            "totalColli": total_qty,
            "totalWeight": total_weight,
            "totalVolume": total_volume
        }]
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post('http://realnexus.comit.cloud:5000/api/Bookings', json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            booking.api_booking_ref = "SUCCESS"
        else:
            print(f"Failed to post booking to API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error posting booking {booking.id} to API: {e}")

@customer.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    recent_shipments = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).limit(5).all()
    total_shipments = Booking.query.filter_by(user_id=current_user.id).count()
    in_transit = Booking.query.filter_by(user_id=current_user.id).filter(Booking.status.contains('Transit')).count()
    delivered = Booking.query.filter_by(user_id=current_user.id, status='Delivered').count()
    pending = Booking.query.filter_by(user_id=current_user.id).filter(Booking.status.contains('Pending')).count()
    booked = Booking.query.filter_by(user_id=current_user.id, status='Booked').count()
    si_needed = Booking.query.filter_by(user_id=current_user.id, status='Booked', is_si_submitted=False).first()

    return render_template('customer/dashboard.html',
                         recent_shipments=recent_shipments,
                         total_active=total_shipments - delivered,
                         total_shipments=total_shipments,
                         in_transit=in_transit,
                         delivered=delivered,
                         pending=pending,
                         booked=booked,
                         si_needed=si_needed,
                         today=datetime.now())

@customer.route('/my_quotes')
@login_required
def my_quotes():
    if current_user.role not in ['customer', 'agent']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    from sqlalchemy import or_
    from datetime import timedelta
    
    quotes = Booking.query.filter(
        Booking.user_id == current_user.id,
        or_(Booking.status == 'Saved Quote', Booking.status == 'Booked')
    ).order_by(Booking.created_at.desc()).all()
    
    quote_data = []
    now = datetime.utcnow()
    
    for q in quotes:
        valid_until = q.created_at + timedelta(days=30)
        
        if q.status == 'Booked':
            computed_status = 'Booked'
        elif valid_until < now:
            computed_status = 'Expired'
        elif (valid_until - now).days <= 2:
            computed_status = 'Expiring Soon'
        else:
            computed_status = 'Active'
            
        quote_data.append({
            'booking': q,
            'computed_status': computed_status,
            'valid_until': valid_until.strftime('%Y-%m-%d')
        })
        
    return render_template('customer/my_quotes.html', quote_data=quote_data)

@customer.route('/save-quote', methods=['POST'])
@login_required
def save_quote():
    if current_user.role not in ['customer', 'agent']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    rate_id = request.form.get('rate_id')
    total_cost = request.form.get('total_cost', 0.0)
    service_type = request.form.get('service_type', 'LCL')
    
    query = session.get('search_query', {})
    origin = query.get('origin', 'Unknown')
    destination = query.get('destination', 'Unknown')
    volume = query.get('volume', 0.0)
    
    rate = None
    if rate_id and str(rate_id).isdigit():
        rate = Rate.query.get(int(rate_id))
        
    nvocc_name = rate.nvocc_name if rate else 'API Quote'

    api_id = query.get('api_quotation_id', '')
    quote_number = query.get('quote_id', api_id or f"QUOTE-{datetime.now().strftime('%M%S')}")

    # POST to Quotations API to get the real quotation number
    import os
    import tempfile
    import requests
    temp_file = os.path.join(tempfile.gettempdir(), f"last_api_response_{current_user.id}.json")
    try:
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
                # Format payload properly for saving the quote
                q_payload = cached_data.get('quotation', cached_data)
                header = q_payload.get('header', q_payload)
                
                # Fix dates to avoid "validUntil must be after validFrom" error
                now = datetime.utcnow()
                from datetime import timedelta
                header['validFrom'] = now.isoformat() + "Z"
                header['validUntil'] = (now + timedelta(days=30)).isoformat() + "Z"

                headers = {'accept': 'application/json', 'x-api-key': '1', 'Content-Type': 'application/json'}
                save_resp = requests.post('http://realnexus.comit.cloud:5000/api/Quotations', json=q_payload, headers=headers, timeout=10)
                if save_resp.status_code in [200, 201]:
                    r_data = save_resp.json()
                    new_id = r_data.get('quotationId')
                    if new_id:
                        quote_number = r_data.get('quotationNo') or r_data.get('quoteNo') or str(new_id)
                        # Update the session with the new real quote ID
                        query['quote_id'] = quote_number
                        query['api_quotation_id'] = new_id
                        session['search_query'] = query
                else:
                    print(f"Failed to save quote via API: {save_resp.status_code} - {save_resp.text}")
    except Exception as e:
        print(f"Error calling POST /api/Quotations: {e}")

    booking = Booking(
        user_id=current_user.id,
        origin=origin,
        destination=destination,
        volume=float(volume) if volume else 0.0,
        selected_nvocc=nvocc_name,
        total_cost=float(total_cost) if total_cost else 0.0,
        service_type=service_type,
        api_booking_ref=quote_number,
        status='Saved Quote'
    )
    db.session.add(booking)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'quote_number': quote_number})
        
    flash('Quote successfully saved!', 'success')
    return redirect(url_for('customer.my_quotes'))

@customer.route('/quote/<int:quote_id>')
@login_required
def quote_detail(quote_id):
    if current_user.role not in ['customer', 'agent']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    quote = Booking.query.filter_by(id=quote_id, user_id=current_user.id, status='Saved Quote').first_or_404()
    
    breakdown = []
    if quote.api_booking_ref:
        import requests
        headers = {'accept': 'application/json', 'x-api-key': '1'}
        try:
            resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{quote.api_booking_ref}", headers=headers, timeout=10)
            if resp.status_code == 200:
                resp_json = resp.json()
                data = resp_json.get('quotation', resp_json)
                tariff = data.get('tariff', data)
                breakdown = tariff.get('lines', [])
            else:
                print(f"API returned {resp.status_code} for {quote.api_booking_ref}: {resp.text}")
        except Exception as e:
            print("Failed to fetch quote breakdown:", e)

    # Fallback to cached API response if available
    if not breakdown:
        import os
        import tempfile
        import json
        temp_file = os.path.join(tempfile.gettempdir(), f"last_api_response_{current_user.id}.json")
        try:
            if os.path.exists(temp_file):
                with open(temp_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    
                    data = cached_data.get('quotation', cached_data)
                    header = data.get('header', data)
                    
                    # Verify if the cached data is somewhat related, or just fallback safely
                    quo_id = header.get('quotationNo') or header.get('quoteNo') or str(header.get('quotationId') or '')
                    
                    if str(header.get('quotationId')) in str(quote.api_booking_ref) or quote.api_booking_ref == quo_id or quote.api_booking_ref.endswith('-'):
                        tariff = data.get('tariff', data)
                        breakdown = tariff.get('lines', [])
        except Exception as e:
            print(f"Failed to load cached quote breakdown: {e}")

    return render_template('customer/quote_detail.html', quote=quote, breakdown=breakdown)

@customer.route('/quote/<int:quote_id>/download_pdf')
@login_required
def download_pdf(quote_id):
    if current_user.role not in ['customer', 'agent']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    quote = Booking.query.filter_by(id=quote_id, user_id=current_user.id, status='Saved Quote').first_or_404()
    
    breakdown = []
    if quote.api_booking_ref:
        import requests
        headers = {'accept': 'application/json', 'x-api-key': '1'}
        try:
            resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{quote.api_booking_ref}", headers=headers, timeout=10)
            if resp.status_code == 200:
                resp_json = resp.json()
                data = resp_json.get('quotation', resp_json)
                tariff = data.get('tariff', data)
                breakdown = tariff.get('lines', [])
        except Exception as e:
            print("Failed to fetch quote breakdown:", e)

    if not breakdown:
        import os
        import tempfile
        import json
        temp_file = os.path.join(tempfile.gettempdir(), f"last_api_response_{current_user.id}.json")
        try:
            if os.path.exists(temp_file):
                with open(temp_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    data = cached_data.get('quotation', cached_data)
                    header = data.get('header', data)
                    quo_id = header.get('quotationNo') or header.get('quoteNo') or str(header.get('quotationId') or '')
                    if str(header.get('quotationId')) in str(quote.api_booking_ref) or quote.api_booking_ref == quo_id or quote.api_booking_ref.endswith('-'):
                        tariff = data.get('tariff', data)
                        breakdown = tariff.get('lines', [])
        except Exception as e:
            pass

    from xhtml2pdf import pisa
    from io import BytesIO
    from flask import make_response

    html_content = render_template('customer/quote_pdf_template.html', quote=quote, breakdown=breakdown)
    
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), dest=pdf)
    
    if pisa_status.err:
        flash('Failed to generate PDF document.', 'danger')
        return redirect(url_for('customer.quote_detail', quote_id=quote_id))
        
    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Quotation_{quote.api_booking_ref or quote.id}.pdf'
    
    return response

@customer.route('/rates', methods=['GET', 'POST'])
@login_required
def rates():
    if current_user.role not in ['customer', 'agent']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        import requests
        
        service_type = request.form.get('service_type', 'LCL').upper()
        goods_types = [g.strip().upper() for g in request.form.getlist('goods_type[]')]
        
        # Extract IDs from User Profile mappings
        branch_id = 1
        customer_id = 1
        if current_user.branches:
            try: branch_id = int(current_user.branches[0].branch_id)
            except: pass
        if current_user.accounts:
            try: customer_id = int(current_user.accounts[0].account_id)
            except: pass
            
        # Build API Payload
        traffic_type = request.form.get("traffic_type") or "EX"
        
        valid_from = request.form.get("cargo_ready_date", "")
        if not valid_from:
            valid_from = datetime.now().strftime("%Y-%m-%d")
        
        try:
            from datetime import timedelta
            valid_from_dt = datetime.strptime(valid_from, "%Y-%m-%d")
        except Exception:
            from datetime import timedelta
            valid_from_dt = datetime.now()
            valid_from = valid_from_dt.strftime("%Y-%m-%d")
            
        valid_until = (valid_from_dt + timedelta(days=30)).strftime("%Y-%m-%d")
        # Extract locodes from origin and destination
        origin_str = request.form.get("origin", "")
        dest_str = request.form.get("destination", "")
        
        import re
        pol_locode = ""
        m_pol = re.search(r'\(([^)]+)\)$', origin_str.strip())
        if m_pol: pol_locode = m_pol.group(1).strip()
        
        pod_locode = ""
        m_pod = re.search(r'\(([^)]+)\)$', dest_str.strip())
        if m_pod: pod_locode = m_pod.group(1).strip()

        # --- API Mapping Rules ---
        # Map UI strings to Realnexus internal lookup codes
        t_mode_val = request.form.get("transport_mode", "").lower()
        t_mode_map = {"ocean": "10", "sea": "10", "air": "40", "road": "30", "rail": "20"}
        mapped_mode = t_mode_map.get(t_mode_val, "10")
        
        svc_val = service_type.upper()
        # ERP expects "10CN" (Container) as the equipment type for both FCL and LCL ocean freight
        mapped_svc = "10CN" 
        
        mov_val = request.form.get("movement_type", "PORT_TO_PORT").upper()
        # Map to ERP standard routing codes (2 = LCL/LCL Port-to-Port, 3 = FCL/FCL)
        mov_map = {
            "DOOR_TO_DOOR": "11",
            "DOOR_TO_PORT": "13",
            "PORT_TO_DOOR": "31",
            "PORT_TO_PORT": "2" if svc_val == "LCL" else "3"
        }
        mapped_mov = mov_map.get(mov_val, "2")

        vas_codes = request.form.getlist('vas_code[]')
        vas_list = []
        for code in vas_codes:
            vas = {"serviceCode": code}
            if code == "INR" or code == "INS": 
                vas["insuredValue"] = float(request.form.get("insurance_amount") or 0.0)
                vas["insuredCurrency"] = request.form.get("insurance_currency", "USD")
            vas_list.append(vas)

        payload = {
            "branchId": branch_id,
            "customerId": customer_id,
            "accountContactId": current_user.id,
            "customerReference": request.form.get("customer_reference") or "WEB-QUOTE",
            "trafficType": traffic_type,
            "freightTransportMode": mapped_mode,
            "freightTransportType": mapped_svc,
            "movementType": mapped_mov,
            "cargoClassification": "11" if "HAZARDOUS" in goods_types else "12",
            "incoterm": request.form.get("freight_terms", ""),
            "validOn": valid_from,
            "currency": request.form.get("currency", "USD"),
            "paymentMethod": request.form.get("payment_terms", ""),
            "specialInstructions": request.form.get("special_instructions", ""),
            "route": {
                "porLocode": "",
                "porLocation": request.form.get("pickup_address", ""),
                "polLocode": pol_locode,
                "polLocation": origin_str,
                "podLocode": pod_locode,
                "podLocation": dest_str,
                "delLocode": "",
                "delLocation": request.form.get("place_of_delivery", ""),
                "pickup": {
                    "location": request.form.get("pickup_address", "")
                },
                "delivery": {
                    "location": request.form.get("place_of_delivery", "")
                }
            },
            "haulageOriginNeeded": bool(request.form.get("pickup_address")),
            "haulageDestinationNeeded": bool(request.form.get("place_of_delivery")),
            "cargo": [],
            "valueAddedServices": vas_list
        }

        if service_type == 'LCL':
            item_qtys = request.form.getlist('item_qty[]')
            item_types = request.form.getlist('item_type[]')
            item_weights = request.form.getlist('item_weight[]')
            item_volumes = request.form.getlist('item_volume[]')
            item_descs = request.form.getlist('item_desc[]')
            
            item_imo_uns = request.form.getlist('item_imo_un[]')
            item_imo_classes = request.form.getlist('item_imo_class[]')
            item_imo_names = request.form.getlist('item_imo_name[]')
            item_imo_groups = request.form.getlist('item_imo_group[]')
            
            for i in range(len(item_qtys)):
                is_haz = (goods_types[i] == 'HAZARDOUS') if i < len(goods_types) else False
                
                # Fetch dimensions for this specific item (taking first entered dim if any)
                dim_pieces = request.form.getlist(f'dim_pieces_cargo-{i+1}[]')
                dim_lengths = request.form.getlist(f'dim_length_cargo-{i+1}[]')
                dim_widths = request.form.getlist(f'dim_width_cargo-{i+1}[]')
                dim_heights = request.form.getlist(f'dim_height_cargo-{i+1}[]')
                
                dim_amt = int(dim_pieces[0]) if dim_pieces and dim_pieces[0] else 0
                dim_len = float(dim_lengths[0]) if dim_lengths and dim_lengths[0] else 0.0
                dim_wid = float(dim_widths[0]) if dim_widths and dim_widths[0] else 0.0
                dim_hgt = float(dim_heights[0]) if dim_heights and dim_heights[0] else 0.0
                
                is_stackable = request.form.get(f'item_stackable_cargo-{i+1}') == "on"

                cargo_item = {
                    "packageType": item_types[i] if i < len(item_types) else "",
                    "packageTypeDescription": item_types[i] if i < len(item_types) else "",
                    "pieceCount": int(item_qtys[i]) if item_qtys[i] else 1,
                    "commodityDescription": item_descs[i] if i < len(item_descs) else "",
                    "weight": float(item_weights[i]) if i < len(item_weights) and item_weights[i] else 0.0,
                    "volume": float(item_volumes[i]) if i < len(item_volumes) and item_volumes[i] else 0.0,
                    "stackable": is_stackable,
                    "dimensions": {"amount": dim_amt, "length": dim_len, "width": dim_wid, "height": dim_hgt},
                    "isHazardous": is_haz
                }
                if is_haz:
                    cargo_item["imo"] = {
                        "un": item_imo_uns[i] if i < len(item_imo_uns) and item_imo_uns[i] else "UNKNOWN", 
                        "class": item_imo_classes[i] if i < len(item_imo_classes) and item_imo_classes[i] else "UNKNOWN", 
                        "properShippingName": item_imo_names[i] if i < len(item_imo_names) and item_imo_names[i] else "UNKNOWN", 
                        "packingGroup": item_imo_groups[i] if i < len(item_imo_groups) and item_imo_groups[i] else "UNKNOWN"
                    }
                payload["cargo"].append(cargo_item)
        else:
            cont_types = request.form.getlist('cont_type[]')
            cont_qtys = request.form.getlist('cont_qty[]')
            c_weights = request.form.getlist('cont_weight[]')
            c_volumes = request.form.getlist('cont_volume[]')
            c_descs = request.form.getlist('cont_desc[]')
            
            for i in range(len(cont_types)):
                is_haz = (goods_types[i] == 'HAZARDOUS') if i < len(goods_types) else False
                cargo_item = {
                    "packageType": cont_types[i] if i < len(cont_types) else "",
                    "packageTypeDescription": cont_types[i] if i < len(cont_types) else "",
                    "pieceCount": int(cont_qtys[i]) if i < len(cont_qtys) and cont_qtys[i] else 1,
                    "commodityDescription": c_descs[i] if i < len(c_descs) else "",
                    "weight": float(c_weights[i]) if i < len(c_weights) and c_weights[i] else 0.0,
                    "volume": float(c_volumes[i]) if i < len(c_volumes) and c_volumes[i] else 0.0,
                    "stackable": True,
                    "dimensions": {"amount": 0, "length": 0, "width": 0, "height": 0},
                    "isHazardous": is_haz
                }
                if is_haz:
                    cargo_item["imo"] = {
                        "un": "UNKNOWN", "class": "UNKNOWN", "properShippingName": "UNKNOWN", "packingGroup": "UNKNOWN"
                    }
                payload["cargo"].append(cargo_item)

        try:
            headers = {'accept': 'application/json', 'x-api-key': '1', 'Content-Type': 'application/json'}
            api_resp = requests.post('http://realnexus.comit.cloud:5000/api/Quotations/request', json=payload, headers=headers, timeout=10)
            
            print("\\n" + "="*50)
            print("REQUEST PAYLOAD:")
            import json as _json
            print(_json.dumps(payload, indent=2))
            print("\\nRAW API RESPONSE:")
            print(api_resp.text)
            print("="*50 + "\\n")
            
            if api_resp.status_code in [200, 201]:
                data = api_resp.json()
                
                # The new API endpoint wraps the response in a "quotation" object containing "header"
                if "quotation" in data and "header" in data["quotation"]:
                    header_data = data["quotation"]["header"]
                else:
                    header_data = data
                    
                quo_id = header_data.get('quotationNo') or header_data.get('quoteNo') or str(header_data.get('quotationId') or '')
                flash(f"Success! Quotation {quo_id} has been created.", "success")
                
                # Mock up the rate results session so the redirect works nicely
                session['search_query'] = {
                    'origin': payload['route']['polLocation'],
                    'destination': payload['route']['podLocation'],
                    'volume': sum(c['volume'] for c in payload['cargo']),
                    'service_type': service_type,
                    'cargo_items': payload['cargo'],
                    'quote_id': quo_id,
                    'api_quotation_id': header_data.get('quotationId', '')
                }
                
                # Store the large payload in a temp file instead of the 4KB-limited session cookie
                import json as _json
                import os
                import tempfile
                temp_file = os.path.join(tempfile.gettempdir(), f"last_api_response_{current_user.id}.json")
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        _json.dump(data, f)
                except Exception as e:
                    print(f"Could not write temp session file: {e}")
                
                return redirect(url_for('customer.rate_results'))
            else:
                print("Constructed Payload:", json.dumps(payload, indent=2))
                print("API ERROR:", api_resp.status_code, api_resp.text)
                flash(f"Failed to create quotation. API responded with status {api_resp.status_code}. Error details: {api_resp.text}", "danger")
                return redirect(url_for('customer.rates'))
        except Exception as e:
            flash(f"API Error: {str(e)}", "danger")
            return redirect(url_for('customer.rates'))
    # Fetch Countries
    from app.services.master_data import get_code_list
    try:
        countries_api = get_code_list('countrycode')
        countries = [c.to_dict() for c in countries_api] if countries_api else []
    except Exception as ex:
        print("Error fetching countries:", ex)
        countries = []

    # Fetch other lookup fields
    try:
        # Fetch from new CodeLists API where supported
        incoterms_api = get_code_list('incoterm')
        incoterms = incoterms_api if incoterms_api else []
        
        package_api = get_code_list('packagecode')
        package_types = [pt.to_dict() for pt in package_api] if package_api else []
        
        container_api = get_code_list('freighttransporttype')
        container_types = [ct.to_dict() for ct in container_api] if container_api else []
        
        # Fetch Value Added Services
        vas_api = get_code_list('vastype')
        vas_types = [c.to_dict() for c in vas_api] if vas_api else []

        # Hardcode basic UOMs and Terms since they are not in the CodeLists API, stripping internal DB dependencies
        weight_uom = [{'code': 'kg', 'name': 'Kilograms (kg)'}, {'code': 'lbs', 'name': 'Pounds (lbs)'}]
        volume_uom = [{'code': 'cbm', 'name': 'Cubic Meters (cbm)'}, {'code': 'cbf', 'name': 'Cubic Feet (cbf)'}]
        freight_terms = [{'code': 'prepaid', 'name': 'Prepaid'}, {'code': 'collect', 'name': 'Collect'}]
    except Exception as ex:
        print("Error fetching lookup lists:", ex)
        incoterms = []
        package_types = []
        container_types = []

        vas_types = []
        weight_uom = []
        volume_uom = []
        freight_terms = []

    return render_template('customer/rates.html',
                         countries=countries,
                         incoterms=incoterms,
                         package_types_json=json.dumps(package_types),
                         container_types_json=json.dumps(container_types),
                         vas_types_json=json.dumps(vas_types),
                         weight_uom_json=json.dumps(weight_uom),
                         volume_uom_json=json.dumps(volume_uom),
                         freight_terms=freight_terms)

@customer.route('/api/get-ports/<direction>/<country_code>')
@login_required
def api_get_ports(direction, country_code):
    import requests
    headers = {'accept': '*/*', 'x-api-key': '1'}
    endpoint = 'OriginPorts' if direction.lower() == 'origin' else 'DestinationPorts'
    url = f"http://realnexus.comit.cloud:5000/api/Ports/{endpoint}/{country_code}"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            ports = resp.json()
            valid_ports = []
            for p in ports:
                if p.get('isActive') and p.get('code'):
                    valid_ports.append({
                        'code': p['code'],
                        'name': p.get('name', p['code']),
                        'country': country_code.upper()
                    })
            return jsonify(valid_ports)
        return jsonify([])
    except Exception as e:
        print(f"Error fetching ports for {country_code}: {e}")
    return jsonify([])


@customer.route('/new-booking', methods=['GET', 'POST'])
@login_required
def new_booking():
    if current_user.role not in ['customer', 'agent']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        service_type = request.form.get('service_type', 'LCL')
        
        cargo_items = []
        total_volume = 0.0
        
        if service_type == 'LCL':
            item_qtys = request.form.getlist('item_qty[]')
            item_types = request.form.getlist('item_type[]')
            item_weights = request.form.getlist('item_weight[]')
            item_volumes = request.form.getlist('item_volume[]')
            
            for i in range(len(item_qtys)):
                vol = float(item_volumes[i]) if i < len(item_volumes) and item_volumes[i] else 0.0
                total_volume += vol
                cargo_items.append({
                    'qty': item_qtys[i],
                    'type': item_types[i],
                    'weight': item_weights[i],
                    'volume': vol
                })
            
            # Use top-level volume if provided and only 1 item, or use sum
            top_vol = request.form.get('volume')
            if top_vol and not total_volume:
                total_volume = float(top_vol)
        else: # FCL
            cont_types = request.form.getlist('cont_type[]')
            cont_qtys = request.form.getlist('cont_qty[]')
            p_qtys = request.form.getlist('cont_p_qty[]')
            p_types = request.form.getlist('cont_p_type[]')
            c_weights = request.form.getlist('cont_weight[]')
            c_volumes = request.form.getlist('cont_volume[]')
            
            for i in range(len(cont_types)):
                vol = float(c_volumes[i]) if i < len(c_volumes) and c_volumes[i] else 0.0
                qty = int(cont_qtys[i]) if i < len(cont_qtys) and cont_qtys[i] else 1
                total_volume += (vol * qty)
                cargo_items.append({
                    'cont_type': cont_types[i],
                    'cont_qty': qty,
                    'p_qty': p_qtys[i] if i < len(p_qtys) else '',
                    'p_type': p_types[i] if i < len(p_types) else '',
                    'weight': c_weights[i] if i < len(c_weights) else '',
                    'volume': vol
                })
        
        # Store in session for results page and pre-filling
        session['search_query'] = {
            'origin': origin,
            'destination': destination,
            'volume': total_volume,
            'service_type': service_type,
            'cargo_items': cargo_items
        }
        
        return redirect(url_for('customer.rate_results'))
        
    # Fetch origins and destinations from Realnexus API
    origins = []
    destinations = []
    try:
        import requests
        headers = {'accept': '*/*', 'x-api-key': '1'}
        
        branch_id = 1
        if current_user.branches:
            try: branch_id = int(current_user.branches[0].branch_id)
            except: pass
            
        traffic_type = "EX"
        
        tl_url = f'http://realnexus.comit.cloud:5000/api/Ports/TransportLanes?branchId={branch_id}&trafficType={traffic_type}'
        tl_resp = requests.get(tl_url, headers=headers, timeout=5)
        if tl_resp.status_code == 200:
            lanes = tl_resp.json()
            for lane in lanes:
                if 'code' in lane and 'name' in lane:
                    val = f"{lane['name']} ({lane['code']})" if lane['code'] else lane['name']
                    if val:
                        origins.append(val)
                        destinations.append(val)
                else:
                    if lane.get('fromUNLocode'): origins.append(lane.get('fromUNLocode'))
                    if lane.get('toUNLocode'): destinations.append(lane.get('toUNLocode'))
            
            origins = list(set(origins))
            destinations = list(set(destinations))
            
            if not origins:
                op_resp = requests.get('http://realnexus.comit.cloud:5000/api/Ports/OriginPorts', headers=headers, timeout=5)
                if op_resp.status_code == 200:
                    for p in op_resp.json():
                        if p.get('isActive') and p.get('name'):
                            origins.append(f"{p['name']} ({p.get('code', '')})")
            if not destinations:
                dp_resp = requests.get('http://realnexus.comit.cloud:5000/api/Ports/DestinationPorts', headers=headers, timeout=5)
                if dp_resp.status_code == 200:
                    for p in dp_resp.json():
                        if p.get('isActive') and p.get('name'):
                            destinations.append(f"{p['name']} ({p.get('code', '')})")
    except Exception as e:
        print("Error fetching ports from API:", e)
        origins = [o[0] for o in db.session.query(Rate.origin).distinct().all() if o[0]]
        destinations = [d[0] for d in db.session.query(Rate.destination).distinct().all() if d[0]]
    
    quote_id = request.args.get('quote_id')
    quote_data = None
    if quote_id:
        quote_data = Booking.query.get(quote_id)
        if quote_data and quote_data.user_id != current_user.id:
            quote_data = None # security check
            
    return render_template('customer/new_booking.html', 
                         origins=origins, 
                         destinations=destinations,
                         query=session.get('search_query', {}),
                         quote_data=quote_data)

@customer.route('/rate-results')
@login_required
def rate_results():
    query = session.get('search_query')
    if not query:
        return redirect(url_for('customer.new_booking'))
        
    api_id = query.get('api_quotation_id')
    results = []
    
    # Try to use the cached API response from the file system
    cached_data = None
    import json as _json
    import os
    import tempfile
    temp_file = os.path.join(tempfile.gettempdir(), f"last_api_response_{current_user.id}.json")
    try:
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='utf-8') as f:
                cached_data = _json.load(f)
    except Exception as e:
        print(f"Failed to load cached API data: {e}")
    
    if api_id or cached_data:
        import requests
        data = None
        
        if api_id:
            headers = {'accept': 'application/json', 'x-api-key': '1'}
            try:
                resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{api_id}", headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json().get('quotation', {})
            except Exception as e:
                flash(f"Error communicating with API: {str(e)}", "danger")
        
        if not data and cached_data:
            data = cached_data.get('quotation', {}) if 'quotation' in cached_data else cached_data
            
        if data:
            try:
                
                header = data.get('header', {})
                sailings = data.get('sailings', [])
                tariff = data.get('tariff', {})
                
                sailing = sailings[0] if sailings else {}
                pol = sailing.get('pol', {})
                pod = sailing.get('pod', {})
                
                # Calculate transit days
                import datetime
                transit_days = 0
                if pol.get('etd') and pod.get('eta'):
                    try:
                        etd = datetime.datetime.strptime(pol['etd'][:10], '%Y-%m-%d')
                        eta = datetime.datetime.strptime(pod['eta'][:10], '%Y-%m-%d')
                        transit_days = (eta - etd).days
                    except:
                        pass
                
                # Calculate total price
                lines = tariff.get('lines', [])
                total_cost = sum(line.get('amount', 0) for line in lines)
                
                is_lcl = query.get('service_type', '') in ['Less than a container load', 'LCL']
                branch_name = 'Fast Transitline Antwerp'
                carrier_name = branch_name if is_lcl else (sailing.get('linerName') or 'Standard Carrier')
                nvocc_name = carrier_name
                
                # Fetch Schedules for Next Closing & Modal
                pol_locode = ""
                m_pol = re.search(r'\(([^)]+)\)$', query.get('origin', '').strip())
                if m_pol: pol_locode = m_pol.group(1).strip()
                
                pod_locode = ""
                m_pod = re.search(r'\(([^)]+)\)$', query.get('destination', '').strip())
                if m_pod: pod_locode = m_pod.group(1).strip()

                schedules = []
                next_closing = None
                
                if pol_locode and pod_locode:
                    try:
                        sched_url = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol_locode}&portOfDischarge={pod_locode}"
                        sched_resp = requests.get(sched_url, headers={'accept': 'application/json', 'x-api-key': '1'}, timeout=5)
                        if sched_resp.status_code == 200:
                            schedules = sched_resp.json()
                            if not isinstance(schedules, list):
                                schedules = []
                    except Exception as e:
                        print(f"Failed to fetch schedules: {e}")

                # Sort schedules and get earliest ETD
                def get_etd(s):
                    return str(s.get('etd') or s.get('estimatedTimeOfDeparture') or '')

                if schedules:
                    # Filter out schedules with no ETD
                    schedules = [s for s in schedules if get_etd(s)]
                    schedules.sort(key=get_etd)
                    if schedules:
                        first_etd = get_etd(schedules[0])
                        try:
                            next_closing = datetime.datetime.strptime(first_etd[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                        except:
                            next_closing = first_etd[:10]

                # Fallback to Quotation POL if Schedules API fails/is empty
                if not next_closing and pol:
                    closing_val = pol.get('closingLcl') if is_lcl else pol.get('closing')
                    if not closing_val:
                        closing_val = pol.get('closing')
                    if closing_val:
                        try:
                            next_closing = datetime.datetime.strptime(closing_val[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                        except:
                            next_closing = closing_val[:10]
                
                # Format to match the frontend expectations while passing real API data
                results = [{
                    'api_quote': data,
                    'total_cost': total_cost,
                    'transit_days': transit_days,
                    'carrier': carrier_name,
                    'frequency': 'API Specific',
                    'ui_tag': 'Official API Quote',
                    'next_closing': next_closing,
                    'schedules': schedules,
                    'rate': {
                        'nvocc_name': nvocc_name,
                        'validity_end': header.get('validUntil', 'N/A'),
                        'id': api_id
                    },
                    'breakdown': lines
                }]
            except Exception as e:
                flash(f"Error processing API quotation data: {str(e)}", "danger")
        else:
            flash("Failed to fetch official quotation details. No valid quotation data found.", "danger")

    return render_template('customer/rate_results.html', results=results, query=query)

@customer.route('/finalize-booking', methods=['GET', 'POST'])
@login_required
def finalize_booking():
    if request.method == 'GET':
        flash('Please start a rate search to place a booking.', 'info')
        return redirect(url_for('customer.new_booking'))
    if current_user.role != 'customer':
        flash('Agents and Administrators cannot place bookings directly.', 'warning')
        return redirect(url_for('customer.rate_results'))
    rate_id = request.form.get('rate_id')
    raw_volume = request.form.get('volume')
    volume = float(raw_volume) if raw_volume else 0.0
    total_cost = float(request.form.get('total_cost') or 0.0)
    service_type = request.form.get('service_type', 'LCL')
    
    query = session.get('search_query', {})
    
    class MockRate:
        pass
    rate = MockRate()
    rate.id = rate_id
    rate.origin = query.get('origin', 'Origin')
    rate.destination = query.get('destination', 'Destination')
    rate.nvocc_name = "API Carrier"

    if rate_id and str(rate_id).isdigit():
        db_rate = Rate.query.get(int(rate_id))
        if db_rate:
            rate = db_rate
            
    return render_template('customer/finalize_booking.html', 
                         rate=rate, 
                         volume=volume, 
                         total_cost=total_cost,
                         service_type=service_type,
                         origin=rate.origin,
                         destination=rate.destination,
                         query=query)

@customer.route('/confirm-booking', methods=['POST'])
@login_required
def confirm_booking():
    rate_id = request.form.get('rate_id')
    raw_volume = request.form.get('volume')
    volume = float(raw_volume) if raw_volume else 0.0
    total_cost = float(request.form.get('total_cost'))
    service_type = request.form.get('service_type', 'LCL')
    pickup_address = request.form.get('pickup_address')
    place_of_receipt = request.form.get('place_of_receipt')
    place_of_delivery = request.form.get('place_of_delivery')
    
    rate = Rate.query.get_or_404(rate_id)
    
    booking = Booking(
        user_id=current_user.id,
        origin=rate.origin,
        destination=rate.destination,
        volume=volume,
        selected_nvocc=rate.nvocc_name,
        total_cost=total_cost,
        service_type=service_type,
        pickup_address=pickup_address,
        place_of_receipt=place_of_receipt,
        place_of_delivery=place_of_delivery,
        freight_terms=request.form.get('freight_terms'),
        general_description=request.form.get('description'),
        general_terms=request.form.get('terms'),
        status='Booked',
        customer_ref=request.form.get('customer_reference'),
        traffic_type=request.form.get('traffic_type')
    )
    
    db.session.add(booking)
    db.session.flush() # Get booking.id
    
    # Process Cargo Items
    process_cargo_items(booking, request.form, service_type)

    # Process Attachments
    save_attachments(booking, request.files.getlist('attachments[]'))
    
    db.session.commit()
    
    # Add initial tracking event
    initial_event = TrackingEvent(
        booking_id=booking.id,
        status='Booked',
        location=rate.origin
    )
    db.session.add(initial_event)
    
    # Fire off API request
    post_booking_to_api(booking)
    
    db.session.commit()
    
    flash('Booking confirmed! You can track your shipment now.', 'success')
    return redirect(url_for('customer.my_shipments'))

@customer.route('/booking-request', methods=['POST'])
@login_required
def booking_request():
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    service_type = request.form.get('service_type', 'LCL')
    
    # Calculate volume from items if not provided as single field
    raw_volume = request.form.get('volume')
    if raw_volume:
        volume = float(raw_volume)
    else:
        volume = 0.0
        if service_type == 'LCL':
            vol_list = request.form.getlist('item_volume[]')
            volume = sum([float(v) for v in vol_list if v])
        else:
            vol_list = request.form.getlist('cont_volume[]')
            qty_list = request.form.getlist('cont_qty[]')
            for i in range(len(vol_list)):
                v = float(vol_list[i]) if vol_list[i] else 0.0
                q = int(qty_list[i]) if i < len(qty_list) and qty_list[i] else 1
                volume += (v * q)
    pickup_address = request.form.get('pickup_address')
    place_of_receipt = request.form.get('place_of_receipt')
    place_of_delivery = request.form.get('place_of_delivery')
    
    provider = 'Manual Entry'
    total_cost = 0.0
    
    booking = Booking(
        user_id=current_user.id,
        origin=origin,
        destination=destination,
        volume=volume,
        selected_nvocc=provider,
        total_cost=total_cost,
        service_type=service_type,
        pickup_address=pickup_address,
        place_of_receipt=place_of_receipt,
        place_of_delivery=place_of_delivery,
        freight_terms=request.form.get('freight_terms'),
        general_description=request.form.get('description'),
        general_terms=request.form.get('terms'),
        status='Pending Review',
        customer_ref=request.form.get('customer_reference'),
        traffic_type=request.form.get('traffic_type')
    )
    
    db.session.add(booking)
    db.session.flush()

    # Process Cargo Items
    process_cargo_items(booking, request.form, service_type)

    # Process Attachments
    save_attachments(booking, request.files.getlist('attachments[]'))

    db.session.commit()
    
    # Add initial tracking event
    initial_event = TrackingEvent(
        booking_id=booking.id,
        status='Pending Review',
        location=origin
    )
    db.session.add(initial_event)
    
    # Fire off API request
    post_booking_to_api(booking)
    
    db.session.commit()
    
    flash('Booking request submitted! We will review it shortly.', 'success')
    return redirect(url_for('customer.my_shipments'))

@customer.route('/my-shipments')
@login_required
def my_shipments():
    shipments = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('customer/shipments.html', shipments=shipments)

@customer.route('/shipment/<int:booking_id>')
@login_required
def shipment_detail(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    return render_template('customer/shipment_detail.html', booking=booking)
@customer.route('/edit-booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    
    # Check if status allows editing
    if booking.status not in ['Booked', 'Pending Review']:
        flash(f'Cannot edit shipment in status: {booking.status}', 'warning')
        return redirect(url_for('customer.shipment_detail', booking_id=booking_id))
    
    if request.method == 'POST':
        booking.origin = request.form.get('origin')
        booking.destination = request.form.get('destination')
        booking.pickup_address = request.form.get('pickup_address')
        booking.place_of_receipt = request.form.get('place_of_receipt')
        booking.place_of_delivery = request.form.get('place_of_delivery')
        booking.freight_terms = request.form.get('freight_terms')
        booking.general_description = request.form.get('description')
        booking.general_terms = request.form.get('terms')
        
        # Clear existing items and re-process
        CargoItem.query.filter_by(booking_id=booking.id).delete()
        process_cargo_items(booking, request.form, booking.service_type)
        
        # Process new attachments if any
        save_attachments(booking, request.files.getlist('attachments[]'))
        
        db.session.commit()
        flash('Shipment updated successfully.', 'success')
        return redirect(url_for('customer.shipment_detail', booking_id=booking.id))
        
    return render_template('customer/edit_booking.html', booking=booking)

import zipfile
import io
from flask import send_file

@customer.route('/shipment/<int:booking_id>/download-doc/<doc_type>')
@login_required
def download_document(booking_id, doc_type):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    
    content = ""
    filename = ""
    
    if doc_type == 'invoice':
        content = f"FREIGHT INVOICE\n---------------\nShipment ID: #{booking.id}\nOrigin: {booking.origin}\nDestination: {booking.destination}\n\nGenerated for demo purposes."
        filename = f"Freight_Invoice_{booking.id}.txt"
    elif doc_type == 'draft_bl':
        content = f"DRAFT BILL OF LADING\n--------------------\nShipper: {booking.shipping_instruction.shipper if booking.shipping_instruction else 'N/A'}\nConsignee: {booking.shipping_instruction.consignee if booking.shipping_instruction else 'N/A'}\n\nDraft generated from SI submission."
        filename = f"Draft_BL_{booking.id}.txt"
    elif doc_type == 'final_bl':
        content = f"FINAL BILL OF LADING\n--------------------\nSerial No: FBL-{booking.id}-XYZ\nStatus: Issued / Original\n\nFinal B/L released for shipment."
        filename = f"Final_BL_{booking.id}.txt"
    else:
        flash('Invalid document type requested.', 'danger')
        return redirect(url_for('customer.shipment_detail', booking_id=booking_id))
        
    memory_file = io.BytesIO(content.encode())
    return send_file(
        memory_file,
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )

@customer.route('/shipment/<int:booking_id>/download-all-docs')
@login_required
def download_all_docs(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    
    # Create ZIP in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Sample documents
        content_invoice = f"COMMERCIAL INVOICE\n------------------\nShipment ID: #{booking.id}\nOrigin: {booking.origin}\nDestination: {booking.destination}\n\nThis is a sample invoice generated for demo purposes."
        content_packing = f"PACKING LIST\n------------\nShipment ID: #{booking.id}\nTotal Items: {len(booking.cargo_items)}\n\nThis is a sample packing list generated for demo purposes."
        content_bl = f"DRAFT BILL OF LADING\n--------------------\nShipper: {booking.shipping_instruction.shipper if booking.shipping_instruction else 'N/A'}\nConsignee: {booking.shipping_instruction.consignee if booking.shipping_instruction else 'N/A'}\n\nThis is a draft B/L generated from Atlas Software integration."
        
        zf.writestr(f"Invoice_{booking.id}.txt", content_invoice)
        zf.writestr(f"Packing_List_{booking.id}.txt", content_packing)
        zf.writestr(f"Draft_BL_{booking.id}.txt", content_bl)
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"Shipment_Documents_{booking.id}.zip"
    )

@customer.route('/shipment/<int:booking_id>/submit-si', methods=['GET', 'POST'])
@login_required
def submit_si(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    
    # Validation: Status and ETD
    if booking.status != 'Booked':
        flash('Shipping Instructions can only be submitted for Booked shipments.', 'warning')
        return redirect(url_for('customer.shipment_detail', booking_id=booking_id))
        
    if booking.etd and datetime.utcnow() > booking.etd:
        flash('Cannot submit SI after Vessel Departure (ETD).', 'danger')
        return redirect(url_for('customer.shipment_detail', booking_id=booking_id))

    if request.method == 'POST':
        # Create or update SI
        si = booking.shipping_instruction
        if not si:
            si = ShippingInstruction(booking_id=booking.id)
            db.session.add(si)
            
        si.shipper = request.form.get('shipper')
        si.consignee = request.form.get('consignee')
        si.notify_party = request.form.get('notify_party')
        si.also_notify = request.form.get('also_notify')
        si.shipper_reference = request.form.get('shipper_reference')
        si.vessel_name = request.form.get('vessel_name')
        si.voyage = request.form.get('voyage')
        si.freight_term = request.form.get('freight_term')
        si.place_of_issue = request.form.get('place_of_issue')
        si.document_type = request.form.get('document_type')
        si.num_originals = int(request.form.get('num_originals', 3))
        si.num_copies = int(request.form.get('num_copies', 0))
        
        # New Weights & VGM Fields
        si.total_gross_weight = float(request.form.get('total_gross_weight', 0)) if request.form.get('total_gross_weight') else 0
        si.net_weight = float(request.form.get('net_weight', 0)) if request.form.get('net_weight') else 0
        si.tare_weight = float(request.form.get('tare_weight', 0)) if request.form.get('tare_weight') else 0
        si.vgm_provided_by = request.form.get('vgm_provided_by')
        si.weighing_method = request.form.get('weighing_method')
        si.vgm_value = float(request.form.get('vgm_value', 0)) if request.form.get('vgm_value') else 0
        
        # Clear existing items and re-process to handle dynamic additions/removals
        # Note: We save marks_numbers specifically in the SI flow
        CargoItem.query.filter_by(booking_id=booking.id).delete()
        
        if booking.service_type == 'LCL':
            qty_list = request.form.getlist('item_qty[]')
            type_list = request.form.getlist('item_type[]')
            weight_list = request.form.getlist('item_weight[]')
            vol_list = request.form.getlist('item_volume[]')
            l_list = request.form.getlist('item_l[]')
            w_list = request.form.getlist('item_w[]')
            h_list = request.form.getlist('item_h[]')
            uom_list = request.form.getlist('item_uom[]')
            hs_list = request.form.getlist('item_hs[]')
            desc_list = request.form.getlist('item_desc[]')
            marks_list = request.form.getlist('item_marks[]')
            is_imo_list = request.form.getlist('item_is_imo[]')
            un_list = request.form.getlist('item_un[]')
            pg_list = request.form.getlist('item_pg[]')
            class_list = request.form.getlist('item_class[]')
            
            for i in range(len(qty_list)):
                item = CargoItem(
                    booking_id=booking.id,
                    quantity=int(qty_list[i]) if qty_list[i] else 0,
                    package_type=type_list[i],
                    weight_kg=float(weight_list[i]) if weight_list[i] else 0.0,
                    volume_cbm=float(vol_list[i]) if vol_list[i] else 0.0,
                    length=float(l_list[i]) if i < len(l_list) and l_list[i] else 0.0,
                    width=float(w_list[i]) if i < len(w_list) and w_list[i] else 0.0,
                    height=float(h_list[i]) if i < len(h_list) and h_list[i] else 0.0,
                    uom=uom_list[i] if i < len(uom_list) else 'cm',
                    hs_code=hs_list[i] if i < len(hs_list) else '',
                    description=desc_list[i] if i < len(desc_list) else '',
                    marks_numbers=marks_list[i] if i < len(marks_list) else '',
                    is_imo=True if i < len(is_imo_list) and is_imo_list[i] == 'yes' else False,
                    un_number=un_list[i] if i < len(un_list) else '',
                    packing_group=pg_list[i] if i < len(pg_list) else '',
                    imo_class=class_list[i] if i < len(class_list) else '',
                    container_no=request.form.getlist('container_no[]')[i] if i < len(request.form.getlist('container_no[]')) else '',
                    seal_no=request.form.getlist('seal_no[]')[i] if i < len(request.form.getlist('seal_no[]')) else ''
                )
                db.session.add(item)
        else: # FCL
            c_qty_list = request.form.getlist('cont_qty[]')
            c_type_list = request.form.getlist('cont_type[]')
            p_qty_list = request.form.getlist('cont_p_qty[]')
            p_type_list = request.form.getlist('cont_p_type[]')
            vol_list = request.form.getlist('cont_volume[]')
            weight_list = request.form.getlist('cont_weight[]')
            hs_list = request.form.getlist('cont_hs[]')
            desc_list = request.form.getlist('cont_desc[]')
            marks_list = request.form.getlist('item_marks[]')
            is_imo_list = request.form.getlist('cont_is_imo[]')
            un_list = request.form.getlist('cont_un[]')
            pg_list = request.form.getlist('cont_pg[]')
            class_list = request.form.getlist('cont_class[]')
            cont_no_list = request.form.getlist('container_no[]')
            seal_no_list = request.form.getlist('seal_no[]')
            
            for i in range(len(c_qty_list)):
                item = CargoItem(
                    booking_id=booking.id,
                    container_count=int(c_qty_list[i]) if c_qty_list[i] else 0,
                    container_type=c_type_list[i],
                    quantity=int(p_qty_list[i]) if p_qty_list[i] else 0,
                    package_type=p_type_list[i],
                    volume_cbm=float(vol_list[i]) if i < len(vol_list) and vol_list[i] else 0.0,
                    weight_kg=float(weight_list[i]) if i < len(weight_list) and weight_list[i] else 0.0,
                    hs_code=hs_list[i] if i < len(hs_list) else '',
                    description=desc_list[i] if i < len(desc_list) else '',
                    marks_numbers=marks_list[i] if i < len(marks_list) else '',
                    is_imo=True if i < len(is_imo_list) and is_imo_list[i] == 'yes' else False,
                    un_number=un_list[i] if i < len(un_list) else '',
                    packing_group=pg_list[i] if i < len(pg_list) else '',
                    imo_class=class_list[i] if i < len(class_list) else '',
                    container_no=cont_no_list[i] if i < len(cont_no_list) else '',
                    seal_no=seal_no_list[i] if i < len(seal_no_list) else ''
                )
                db.session.add(item)
        
        booking.is_si_submitted = True
        db.session.commit()
        
        flash('Shipping Instructions submitted successfully!', 'success')
        return redirect(url_for('customer.shipment_detail', booking_id=booking_id))
        
    # Constants for template
    pkg_types = ['Crate', 'Bag', 'Drum', 'Roll', 'Tube', 'Bundle', 'Skid', 'Pallet', 'Box', 'Case', 'Carton', 'Colis']
    cont_types = ["20' ST", "40' ST", "40' HC", "20' RF", "40' RF", "20' FR", "40' FR", "20' OT", "40' OT"]
        
    return render_template('customer/submit_si.html', 
                         booking=booking,
                         pkg_types=pkg_types,
                         cont_types=cont_types)

