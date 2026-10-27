from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify, send_file, abort
from flask_login import login_required, current_user
from app.models.models import Rate, Booking, TrackingEvent, CargoItem, BookingAttachment, ShippingInstruction
from app.services.rate_engine import RateEngine
from app import db
from datetime import datetime
import os
import io
from werkzeug.utils import secure_filename
import json
import requests
import re
import time

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

def get_booking_safely(ref_or_id, user_id=None, status=None):
    """Safely retrieves a Booking record without SQL Server type conversion errors (SQL Server 245)."""
    if not ref_or_id:
        return None
    ref_str = str(ref_or_id).strip()
    if not ref_str:
        return None

    query = Booking.query
    if user_id is not None:
        query = query.filter(Booking.user_id == user_id)
    if status is not None:
        query = query.filter(Booking.status == status)

    if ref_str.isdigit():
        b = query.filter(Booking.id == int(ref_str)).first()
        if b:
            return b

    return query.filter(
        (Booking.api_booking_ref == ref_str) | (Booking.uuid == ref_str)
    ).first()

def _parse_cc(loc_str, hint=None):
    if hint and len(hint) == 2:
        return hint.upper()
    if not loc_str:
        return hint or ''
    loc = str(loc_str).strip()
    m = re.search(r'\(([A-Za-z]{2})[A-Za-z0-9]{3}\)', loc)
    if m:
        return m.group(1).upper()
    u = re.search(r'\b([A-Za-z]{2})[A-Za-z0-9]{3}\b', loc)
    if u:
        return u.group(1).upper()
    city_map = {
        'antwerp': 'BE', 'singapore': 'SG', 'rotterdam': 'NL', 'hamburg': 'DE',
        'shanghai': 'CN', 'ningbo': 'CN', 'busan': 'KR', 'nhava sheva': 'IN',
        'mundra': 'IN', 'chennai': 'IN', 'barcelona': 'ES', 'valencia': 'ES',
        'le havre': 'FR', 'felixstowe': 'GB', 'genoa': 'IT', 'jebel ali': 'AE',
        'dubai': 'AE', 'los angeles': 'US', 'new york': 'US'
    }
    for k, v in city_map.items():
        if k in loc.lower():
            return v
    return hint or ''

def post_booking_to_api(booking_id):
    try:
        booking = get_booking_safely(booking_id)
        if not booking:
            print(f"Booking {booking_id} not found in database for API post.")
            return
            
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
            db.session.commit()
            print(f"Booking {booking_id} successfully posted to API.")
        else:
            print(f"Failed to post booking {booking_id} to API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error posting booking {booking_id} to API: {e}")

@customer.route('/dashboard')
@login_required
def dashboard():
    if current_user.role in ('super_admin', 'customer_admin'):
        return redirect(url_for('admin.dashboard'))

    return render_template('customer/dashboard.html', today=datetime.now())

def _direct_document_url(url):
    """Turn Google Drive / Docs share links into direct file URLs; other URLs are returned unchanged."""
    m = re.search(r'docs\.google\.com/(document|spreadsheets|presentation)/d/([\w-]+)', url)
    if m:
        return f'https://docs.google.com/{m.group(1)}/d/{m.group(2)}/export?format=pdf'
    m = (re.search(r'drive\.google\.com/file/d/([\w-]+)', url)
         or re.search(r'drive\.google\.com/(?:open|uc)\?(?:.*&)?id=([\w-]+)', url))
    if m:
        return f'https://drive.google.com/uc?export=download&confirm=t&id={m.group(1)}'
    return url

@customer.route('/terms-conditions')
@login_required
def terms_conditions():
    """Serve the configured T&C document from our own origin so the source URL stays hidden."""
    from app import get_cached_system_settings
    from flask import Response
    terms_url = get_cached_system_settings(current_user).get('terms_conditions_url', '')
    if not terms_url:
        return Response('<p style="font-family:sans-serif;padding:2rem;color:#64748b;">Terms &amp; conditions are not configured.</p>',
                        mimetype='text/html')
    fetch_url = _direct_document_url(terms_url)
    try:
        upstream = requests.get(fetch_url, timeout=20)
        upstream.raise_for_status()
    except Exception as e:
        print(f"Error fetching terms & conditions: {e}")
        return Response('<p style="font-family:sans-serif;padding:2rem;color:#64748b;">Terms &amp; conditions could not be loaded. Please try again later.</p>',
                        mimetype='text/html', status=502)

    content_type = upstream.headers.get('Content-Type', 'application/octet-stream')
    body = upstream.content
    if body[:5] == b'%PDF-':
        # Hosts like Google Drive send PDFs as octet-stream, which browsers download instead of display
        content_type = 'application/pdf'
    elif 'text/html' in content_type:
        # Keep relative links/styles of the source page working when served from here
        html = upstream.text
        from markupsafe import escape
        base_tag = f'<base href="{escape(terms_url)}">'
        if re.search(r'<head[^>]*>', html, re.I):
            html = re.sub(r'<head[^>]*>', lambda m: m.group(0) + base_tag, html, count=1, flags=re.I)
        else:
            html = base_tag + html
        body = html.encode('utf-8')
        content_type = 'text/html; charset=utf-8'

    resp = Response(body, mimetype=None, content_type=content_type)
    resp.headers['Content-Disposition'] = 'inline'
    resp.headers['Cache-Control'] = 'private, max-age=600'
    return resp

_DASHBOARD_STATS_CACHE = {
    'expires_at': 0,
    'data': None
}

def _resolve_customer_account_id(default=4128):
    req_acc = request.args.get('accountId') or request.args.get('account_id')
    if req_acc:
        try:
            return int(req_acc)
        except Exception:
            pass
    if hasattr(current_user, 'accounts') and current_user.accounts:
        for a in current_user.accounts:
            try:
                acc_val = int(a.account_id)
                if acc_val in [4128, 4300]:
                    return acc_val
            except Exception:
                pass
        try:
            return int(current_user.accounts[0].account_id)
        except Exception:
            pass
    return default

def _get_candidate_account_ids(primary_default=4128):
    candidates = []
    req_acc = request.args.get('accountId') or request.args.get('account_id')
    if req_acc:
        try: candidates.append(int(req_acc))
        except Exception: pass
    if hasattr(current_user, 'accounts') and current_user.accounts:
        for a in current_user.accounts:
            try:
                val = int(a.account_id)
                if val not in candidates:
                    candidates.append(val)
            except Exception:
                pass
    for default_acc in [primary_default, 4128, 4300, 4294]:
        if default_acc not in candidates:
            candidates.append(default_acc)
    return candidates

@customer.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    now = time.time()
    if _DASHBOARD_STATS_CACHE['data'] is not None and now < _DASHBOARD_STATS_CACHE['expires_at']:
        return jsonify(_DASHBOARD_STATS_CACHE['data'])

    account_id = _resolve_customer_account_id(4128)
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    items = []
    
    try:
        url = "http://realnexus.comit.cloud:5000/api/Bookings"
        resp = requests.get(url, params={"accountId": account_id, "pageSize": 100}, headers=headers, timeout=5)
        if resp.status_code == 200:
            raw_bookings = resp.json().get('bookings', [])
            items = [ApiBookingItem(b) for b in raw_bookings]
    except Exception as e:
        current_app.logger.error(f"Error fetching API bookings for dashboard stats: {e}")

    total_shipments = len(items)
    in_transit = sum(1 for it in items if it.status == 'In Transit')
    delivered = sum(1 for it in items if it.status == 'Delivered')
    booked = sum(1 for it in items if it.status in ['Confirmed', 'Booked'])
    pending = sum(1 for it in items if 'Pending' in (it.status or ''))

    recent_shipments = []
    for it in items[:5]:
        b_ref = it.bookingref or str(it.id)
        recent_shipments.append({
            'id': b_ref,
            'origin': it.origin,
            'destination': it.destination,
            'service_type': it.service_type or 'LCL/LCL',
            'selected_nvocc': it.vessel or 'Direct',
            'status': it.status,
            'created_at': it.created_at.strftime('%d %b %Y') if it.created_at else ''
        })

    result = {
        'total_shipments': total_shipments,
        'total_active': total_shipments - delivered,
        'in_transit': in_transit,
        'pending': pending,
        'delivered': delivered,
        'booked': booked,
        'si_needed': None,
        'recent_shipments': recent_shipments
    }
    _DASHBOARD_STATS_CACHE['data'] = result
    _DASHBOARD_STATS_CACHE['expires_at'] = now + 30
    return jsonify(result)


@customer.route('/my_quotes')
@login_required
def my_quotes():
    if current_user.role != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    return render_template('customer/my_quotes.html')

@customer.route('/api/my-quotes')
@login_required
def api_my_quotes():
    from sqlalchemy import or_
    from datetime import timedelta, datetime
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    customer_id = 1
    if current_user.accounts:
        try: customer_id = int(current_user.accounts[0].account_id)
        except: pass
        
    global _GLOBAL_BRANCHES_CACHE
    if not globals().get('_GLOBAL_BRANCHES_CACHE'):
        globals()['_GLOBAL_BRANCHES_CACHE'] = {}
        try:
            b_resp = requests.get("http://realnexus.comit.cloud:5000/api/Branches/Branches", headers={'x-api-key': '1'}, timeout=2)
            if b_resp.status_code == 200:
                for b in b_resp.json():
                    globals()['_GLOBAL_BRANCHES_CACHE'][str(b.get('branchID') or b.get('branchId', ''))] = b.get('name', '')
        except Exception as e:
            print("Failed to fetch branches:", e)
    all_branches = globals().get('_GLOBAL_BRANCHES_CACHE', {})
        
    quote_data = []
    total_count = 0
    api_success = False
    
    # Try calling Atlas api/Quotations
    try:
        url = "http://realnexus.comit.cloud:5000/api/Quotations"
        params = {
            "accountId": customer_id,
            "page": page,
            "pageSize": per_page
        }
        if request.args.get('reference'):
            params['reference'] = request.args.get('reference')
        if request.args.get('validOn'):
            params['validOn'] = request.args.get('validOn')
        if request.args.get('trafficType'):
            params['trafficType'] = request.args.get('trafficType')
            
        headers = {'accept': 'application/json', 'x-api-key': '1'}
        resp = requests.get(url, params=params, headers=headers, timeout=4)
        
        if resp.status_code == 200:
            data = resp.json()
            items = []
            
            if isinstance(data, list):
                items = data
                total_count = len(data)
            elif isinstance(data, dict):
                items = data.get('items', data.get('quotations', data.get('quotes', [])))
                total_count = data.get('pagination', {}).get('totalRecords', data.get('totalCount', data.get('total', len(items))))
                
            now = datetime.utcnow()
            
            # Pre-fetch detailed quotation data in parallel to resolve complete commodities & weight
            import concurrent.futures
            global _GLOBAL_QUOTE_DETAILS_CACHE
            if '_GLOBAL_QUOTE_DETAILS_CACHE' not in globals():
                globals()['_GLOBAL_QUOTE_DETAILS_CACHE'] = {}
            quote_cache = globals()['_GLOBAL_QUOTE_DETAILS_CACHE']

            quote_details_map = {}
            def _fetch_detail(it):
                # If commodities or tariff lines already exist, detail request is not needed
                if isinstance(it, dict) and (it.get('commodities') or it.get('tariff', {}).get('lines')):
                    return None, {}
                header_obj = it.get('quotation', it).get('header', it)
                q_num = header_obj.get('quoteNumber') or header_obj.get('quotationNo')
                q_id = header_obj.get('quotationId')
                ref_cand = q_num or (f"QUO-2026-{q_id}" if q_id else None)
                if not ref_cand:
                    return None, {}
                if ref_cand in quote_cache:
                    return ref_cand, quote_cache[ref_cand]
                try:
                    r_det = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{ref_cand}?accountId={customer_id}", headers=headers, timeout=1.5)
                    if r_det.status_code == 200:
                        det = r_det.json().get('quotation', {})
                        if det:
                            quote_cache[ref_cand] = det
                        return ref_cand, det
                except Exception:
                    pass
                return ref_cand, {}

            try:
                items_needing_detail = [
                    it for it in items 
                    if not (isinstance(it, dict) and (it.get('commodities') or it.get('tariff', {}).get('lines')))
                ]
                if items_needing_detail:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(items_needing_detail) or 1)) as executor:
                        detail_results = list(executor.map(_fetch_detail, items_needing_detail))
                        for ref_key, det in detail_results:
                            if ref_key and det:
                                quote_details_map[ref_key] = det
            except Exception as ex:
                print(f"Parallel quote details fetch error: {ex}")

            PKG_MAP = {
                'BX': 'Box', 'PX': 'Pallet', 'CR': 'Crate', 'DR': 'Drum', 'BG': 'Bag',
                'ZR': 'IBC', 'CT': 'Carton', 'CTN': 'Carton', 'CS': 'Case', 'CL': 'Colis',
                'SK': 'Skid', 'RL': 'Roll', '20CN': "20' Container", '40CN': "40' Container"
            }

            for item in items:
                q_item = item.get('quotation', item)
                header = q_item.get('header', q_item)
                tariff = q_item.get('tariff', {}) or {}
                lines = tariff.get('lines', []) or []
                
                quote_id = header.get('quotationId')
                prefix1 = header.get('quoPrefix1', 'QUO')
                prefix2 = header.get('quoPrefix2', '2026')
                api_booking_ref = header.get('quoteNumber') or header.get('quotationNo') or f"{prefix1}-{prefix2}-{quote_id}"
                
                detail_obj = quote_details_map.get(api_booking_ref, {}) or quote_details_map.get(quote_id, {})
                if not lines:
                    lines = detail_obj.get('tariff', {}).get('lines', []) or []

                routing = header.get('routing', header.get('route', {})) or {}
                if not routing and isinstance(q_item.get('routing'), dict):
                    routing = q_item.get('routing')
                if not routing and isinstance(item.get('routing'), dict):
                    routing = item.get('routing')

                por_location = str(
                    routing.get('porLocation') or routing.get('porlocation') or
                    header.get('porLocation') or header.get('porlocation') or
                    item.get('porLocation') or item.get('porlocation') or ''
                ).strip()
                pol_location = str(
                    routing.get('polLocation') or routing.get('pollocation') or
                    header.get('polLocation') or header.get('pollocation') or
                    item.get('polLocation') or item.get('pollocation') or ''
                ).strip()

                del_location = str(
                    routing.get('delLocation') or routing.get('dellocation') or
                    header.get('delLocation') or header.get('dellocation') or
                    item.get('delLocation') or item.get('dellocation') or ''
                ).strip()
                pod_location = str(
                    routing.get('podLocation') or routing.get('podlocation') or
                    header.get('podLocation') or header.get('podlocation') or
                    item.get('podLocation') or item.get('podlocation') or ''
                ).strip()

                # ISNULL("porlocation","pollocation") & ISNULL("dellocation","podlocation")
                origin = por_location if por_location else (pol_location if pol_location else "Unknown")
                destination = del_location if del_location else (pod_location if pod_location else "Unknown")
                
                created_on = header.get('createdOn')
                try:
                    if created_on and 'T' in str(created_on):
                        cleaned_created = re.sub(r'\.\d+Z$', 'Z', str(created_on))
                        if not cleaned_created.endswith('Z') and '+' not in cleaned_created:
                            cleaned_created += 'Z'
                        created_at = datetime.fromisoformat(cleaned_created.replace('Z', '+00:00'))
                    elif created_on:
                        created_at = datetime.strptime(str(created_on)[:10], '%Y-%m-%d')
                    else:
                        created_at = now
                except Exception:
                    created_at = now

                # Valid From resolution
                valid_from_raw = (
                    header.get('validFrom') or header.get('validfrom') or
                    item.get('validFrom') or item.get('validfrom') or
                    q_item.get('validFrom') or created_on
                )
                valid_from = ""
                if valid_from_raw:
                    try:
                        if 'T' in str(valid_from_raw):
                            cleaned_vf = re.sub(r'\.\d+Z$', 'Z', str(valid_from_raw))
                            if not cleaned_vf.endswith('Z') and '+' not in cleaned_vf:
                                cleaned_vf += 'Z'
                            vf_dt = datetime.fromisoformat(cleaned_vf.replace('Z', '+00:00'))
                        else:
                            vf_dt = datetime.strptime(str(valid_from_raw)[:10], '%Y-%m-%d')
                        valid_from = vf_dt.strftime('%Y-%m-%d')
                    except Exception:
                        valid_from = str(valid_from_raw)[:10]
                if not valid_from:
                    valid_from = created_at.strftime('%Y-%m-%d')
                    
                valid_until_str = header.get('validUntil') or header.get('validuntil') or item.get('validUntil')
                try:
                    if valid_until_str and 'T' in str(valid_until_str):
                        cleaned_until = re.sub(r'\.\d+Z$', 'Z', str(valid_until_str))
                        if not cleaned_until.endswith('Z') and '+' not in cleaned_until:
                            cleaned_until += 'Z'
                        valid_until_dt = datetime.fromisoformat(cleaned_until.replace('Z', '+00:00'))
                    elif valid_until_str:
                        valid_until_dt = datetime.strptime(str(valid_until_str)[:10], '%Y-%m-%d')
                    else:
                        valid_until_dt = created_at + timedelta(days=30)
                    valid_until = valid_until_dt.strftime('%Y-%m-%d')
                except Exception:
                    valid_until_dt = created_at + timedelta(days=30)
                    valid_until = valid_until_dt.strftime('%Y-%m-%d')
                    
                total_cost = 0.0
                for line in lines:
                    try:
                        amt = float(line.get('amount') or 0.0)
                        total_cost += amt
                    except (ValueError, TypeError):
                        pass

                if not total_cost or total_cost <= 0:
                    for src in [item, q_item, header, tariff, detail_obj]:
                        if isinstance(src, dict):
                            for key in ['totalAmount', 'totalCost', 'amount', 'grandTotal', 'totalamount']:
                                val = src.get(key)
                                if val is not None:
                                    try:
                                        t_val = float(val)
                                        if t_val > 0:
                                            total_cost = t_val
                                            break
                                    except (ValueError, TypeError):
                                        pass
                            if total_cost > 0:
                                break
                    
                local_booking = Booking.query.filter_by(api_booking_ref=api_booking_ref).first()
                status = local_booking.status if local_booking else "Saved Quote"
                local_id = local_booking.id if local_booking else quote_id
                
                if status == 'Booked':
                    computed_status = 'Booked'
                elif valid_until_dt < now:
                    computed_status = 'Expired'
                elif (valid_until_dt - now).days <= 2:
                    computed_status = 'Expiring Soon'
                else:
                    computed_status = 'Active'
                    
                quote_currency = header.get('currency') or item.get('currency') or q_item.get('currency') or tariff.get('quotationCurrency') or ''
                
                # Resolve cargo details for quote card & table display
                c_vol = 0.0
                c_weight = 0.0
                c_packages = ""
                c_desc = ""

                if local_booking:
                    c_vol = float(local_booking.volume or 0.0)
                    if local_booking.cargo_items:
                        c_weight = sum(float(ci.weight_kg or 0.0) for ci in local_booking.cargo_items)
                        pkg_parts = [f"{ci.quantity} x {PKG_MAP.get(str(ci.package_type or '').upper(), ci.package_type or 'Pkg')}" for ci in local_booking.cargo_items if ci.quantity]
                        c_packages = ", ".join(pkg_parts)
                        c_desc = local_booking.cargo_items[0].description if local_booking.cargo_items else ""

                commodities = detail_obj.get('commodities', []) or q_item.get('commodities', []) or header.get('commodities', []) or item.get('commodities', [])
                if not c_vol and commodities:
                    c_vol = sum(float(cm.get('volume') or 0.0) for cm in commodities)
                if not c_weight and commodities:
                    c_weight = sum(float(cm.get('weight') or 0.0) for cm in commodities)
                if not c_packages and commodities:
                    pkg_parts = []
                    for cm in commodities:
                        p_code = (cm.get('packageCode') or cm.get('packageTypeDescription') or 'Pkg').upper()
                        p_label = PKG_MAP.get(p_code, p_code.capitalize())
                        n_pkg = cm.get('nrPackages') or 1
                        pkg_parts.append(f"{n_pkg} x {p_label}")
                    c_packages = ", ".join(pkg_parts)

                # Explicit totalColli (#pkgs)
                total_colli = (
                    header.get('totalColli') or header.get('totalcolli') or
                    item.get('totalColli') or item.get('totalcolli') or
                    q_item.get('totalColli') or q_item.get('totalcolli') or
                    detail_obj.get('totalColli') or detail_obj.get('totalcolli')
                )
                if total_colli is None or total_colli == '' or total_colli == 0:
                    if commodities:
                        try:
                            total_colli = sum(int(cm.get('nrPackages') or 0) for cm in commodities)
                        except Exception:
                            pass
                if (total_colli is None or total_colli == '' or total_colli == 0) and local_booking and local_booking.cargo_items:
                    total_colli = sum(int(ci.quantity or 0) for ci in local_booking.cargo_items)
                try:
                    total_colli = int(total_colli or 0)
                except Exception:
                    total_colli = 0

                # Explicit totalWeight
                total_weight = (
                    header.get('totalWeight') or header.get('totalweight') or
                    item.get('totalWeight') or item.get('totalweight') or
                    q_item.get('totalWeight') or q_item.get('totalweight') or
                    detail_obj.get('totalWeight') or detail_obj.get('totalweight')
                )
                if total_weight is None or total_weight == '' or total_weight == 0:
                    total_weight = c_weight
                try:
                    total_weight = float(total_weight or 0.0)
                except Exception:
                    total_weight = 0.0

                # Explicit totalVolume
                total_volume = (
                    header.get('totalVolume') or header.get('totalvolume') or
                    item.get('totalVolume') or item.get('totalvolume') or
                    q_item.get('totalVolume') or q_item.get('totalvolume') or
                    detail_obj.get('totalVolume') or detail_obj.get('totalvolume')
                )
                if total_volume is None or total_volume == '' or total_volume == 0:
                    total_volume = c_vol
                try:
                    total_volume = float(total_volume or 0.0)
                except Exception:
                    total_volume = 0.0

                # Charge determination logic based on FC, LC, and trafficType
                t_type_mq = (header.get('trafficType') or item.get('trafficType') or 'EX').upper()
                has_fc_mq = any(
                    (l.get('articleCostGroup') or '').upper() == 'FC'
                    or 'FREIGHT' in (l.get('articleName') or '').upper()
                    or 'OCEAN' in (l.get('articleName') or '').upper()
                    for l in lines
                )
                # Freight Charge (FC) represents ocean freight; if present, Freight & Surcharges shown as included
                has_freight_surcharges = has_fc_mq if lines else True

                has_lc_mq = any(
                    (l.get('articleCostGroup') or '').upper() in ['LC', 'OLC', 'DC', 'DLC']
                    or l.get('isLocalCharge') is True
                    for l in lines
                )

                if t_type_mq == 'EX':
                    has_origin_charges = has_lc_mq if lines else True
                    has_dest_charges = any((l.get('articleCostGroup') or '').upper() in ['DC', 'DLC'] for l in lines)
                elif t_type_mq == 'IM':
                    has_origin_charges = any((l.get('articleCostGroup') or '').upper() in ['OLC'] for l in lines)
                    has_dest_charges = has_lc_mq if lines else True
                else:
                    has_origin_charges = has_lc_mq if lines else True
                    has_dest_charges = False

                
                q_branch_id = header.get('branchId') or header.get('branchID') or (current_user.branches[0].branch_id if current_user.branches else '')
                offering_branch = all_branches.get(str(q_branch_id)) or ''

                quote_data.append({
                    'id': local_id,
                    'quotenumber': api_booking_ref,
                    'quote_number': api_booking_ref,
                    'porlocation': por_location,
                    'pollocation': pol_location,
                    'dellocation': del_location,
                    'podlocation': pod_location,
                    'origin': origin,
                    'destination': destination,
                    'total_cost': total_cost,
                    'totalAmount': round(total_cost, 2),
                    'total_amount': round(total_cost, 2),
                    'totalcolli': total_colli,
                    'total_colli': total_colli,
                    'totalweight': round(total_weight, 2),
                    'total_weight': round(total_weight, 2),
                    'totalVolume': round(total_volume, 2),
                    'total_volume': round(total_volume, 2),
                    'validFrom': valid_from,
                    'valid_from': valid_from,
                    'currency': quote_currency,
                    'offering_branch': offering_branch,
                    'selected_nvocc': header.get('nvoccName') or header.get('carrierName') or offering_branch or '',
                    'service_type': "LCL" if "LCL" in str(header.get('freightTransportType') or item.get('freightType') or '').upper() else ("FCL" if "FCL" in str(header.get('freightTransportType') or item.get('freightType') or '').upper() else ""),
                    'service_name': header.get('serviceName') or header.get('serviceLevel') or '',
                    'api_booking_ref': api_booking_ref,
                    'created_at': created_at.strftime('%d %b %Y'),
                    'status': status,
                    'computed_status': computed_status,
                    'valid_until': valid_until,
                    'validUntil': valid_until,
                    'volume': f"{total_volume:.2f}" if total_volume > 0 else (f"{c_vol:.2f}" if c_vol > 0 else ""),
                    'weight': f"{total_weight:,.2f}" if total_weight > 0 else (f"{c_weight:,.2f}" if c_weight > 0 else ""),
                    'packages': f"{total_colli} pkgs" if total_colli > 0 else c_packages,
                    'commodity': c_desc,
                    'has_origin_charges': has_origin_charges,
                    'has_freight_surcharges': has_freight_surcharges,
                    'has_dest_charges': has_dest_charges
                })
            api_success = True
            
    except Exception as e:
        print(f"Error fetching from Quotations API: {e}")
        
    if not api_success:
        # Fallback to local sqlite
        pagination = Booking.query.filter(
            Booking.user_id == current_user.id,
            or_(Booking.status == 'Saved Quote', Booking.status == 'Booked')
        ).order_by(Booking.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        quote_data = []
        now = datetime.utcnow()
        for q in pagination.items:
            valid_until_dt = q.created_at + timedelta(days=30)
            valid_until = valid_until_dt.strftime('%Y-%m-%d')
            valid_from = q.created_at.strftime('%Y-%m-%d')
            if q.status == 'Booked':
                computed_status = 'Booked'
            elif valid_until_dt < now:
                computed_status = 'Expired'
            elif (valid_until_dt - now).days <= 2:
                computed_status = 'Expiring Soon'
            else:
                computed_status = 'Active'
                
            c_vol = float(q.volume or 0.0)
            c_weight = sum(float(ci.weight_kg or 0.0) for ci in q.cargo_items) if q.cargo_items else 0.0
            total_colli = sum(int(ci.quantity or 0) for ci in q.cargo_items) if q.cargo_items else 0
            pkg_parts = [f"{ci.quantity} x {ci.package_type or 'Pkg'}" for ci in q.cargo_items if ci.quantity] if q.cargo_items else []
            c_packages = ", ".join(pkg_parts) if pkg_parts else (f"{total_colli} pkgs" if total_colli > 0 else "")
            c_desc = q.cargo_items[0].description if q.cargo_items else ""

            # Charge inclusion determination for local quote record
            fb_traffic = (getattr(q, 'traffic_type', None) or 'EX').upper()
            if fb_traffic == 'IM':
                fb_origin = False
                fb_freight = True
                fb_dest = True
            else:
                fb_origin = True
                fb_freight = True
                fb_dest = False

            q_num = q.api_booking_ref or f"Local-{q.id}"
            quote_data.append({
                'id': q.id,
                'quotenumber': q_num,
                'quote_number': q_num,
                'porlocation': getattr(q, 'por_location', '') or '',
                'pollocation': q.origin or '',
                'dellocation': getattr(q, 'del_location', '') or '',
                'podlocation': q.destination or '',
                'origin': q.origin,
                'destination': q.destination,
                'total_cost': float(q.total_cost or 0.0),
                'totalAmount': round(float(q.total_cost or 0.0), 2),
                'total_amount': round(float(q.total_cost or 0.0), 2),
                'totalcolli': total_colli,
                'total_colli': total_colli,
                'totalweight': round(c_weight, 2),
                'total_weight': round(c_weight, 2),
                'totalVolume': round(c_vol, 2),
                'total_volume': round(c_vol, 2),
                'validFrom': valid_from,
                'valid_from': valid_from,
                'validUntil': valid_until,
                'valid_until': valid_until,
                'currency': getattr(q, 'currency', 'USD') or 'USD',
                'selected_nvocc': q.selected_nvocc or 'Local Quote',
                'service_type': q.service_type,
                'service_name': getattr(q, 'service_name', None) or 'Direct Service',
                'api_booking_ref': q_num,
                'created_at': q.created_at.strftime('%d %b %Y'),
                'status': q.status,
                'computed_status': computed_status,
                'volume': f"{c_vol:.2f}" if c_vol > 0 else "",
                'weight': f"{c_weight:.2f}" if c_weight > 0 else "",
                'packages': c_packages,
                'commodity': c_desc,
                'has_origin_charges': fb_origin,
                'has_freight_surcharges': fb_freight,
                'has_dest_charges': fb_dest
            })
        total_count = pagination.total

    return jsonify({
        'quotes': quote_data,
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'pages': (total_count + per_page - 1) // per_page if per_page else 0,
        'has_prev': page > 1,
        'has_next': page < ((total_count + per_page - 1) // per_page if per_page else 0)
    })

@customer.route('/save-quote', methods=['POST'])
@login_required
def save_quote():
    if current_user.role != 'customer':
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
    quote_number = None

    # POST to Quotations API to get the real quotation number
    import os
    import tempfile
    import requests
    temp_file = os.path.join(tempfile.gettempdir(), f"last_api_response_{current_user.id}.json")
    api_saved_successfully = False
    error_msg = "Failed to save quote via API. No valid quotation data or API response found."
    uuid_val = None
    
    try:
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
                # Format payload properly for saving the quote (UUID-based flow)
                q_item = cached_data.get('quotation', cached_data)
                header = q_item.get('header', q_item)
                uuid_val = header.get('uuid') or cached_data.get('uuid')
                
                branch_id = 1
                customer_id = 1
                if current_user.branches:
                    try: branch_id = int(current_user.branches[0].branch_id)
                    except: pass
                if current_user.accounts:
                    try: customer_id = int(current_user.accounts[0].account_id)
                    except: pass

                q_payload = {
                    "uuid": uuid_val,
                    "customerId": customer_id,
                    "branchId": branch_id
                }

                print("\n" + "="*50)
                print("SAVING QUOTE PAYLOAD:")
                print(json.dumps(q_payload, indent=2))
                print("="*50 + "\n")

                headers = {'accept': 'application/json', 'x-api-key': '1', 'Content-Type': 'application/json'}
                save_resp = requests.post('http://realnexus.comit.cloud:5000/api/Quotations', json=q_payload, headers=headers, timeout=10)
                
                print("\n" + "="*50)
                print("SAVE RESPONSE:", save_resp.status_code)
                print(save_resp.text)
                print("="*50 + "\n")
                if save_resp.status_code in [200, 201]:
                    r_data = save_resp.json()
                    
                    # Unwrap if the API response is wrapped in "quotation" or "header"
                    header_data = r_data
                    if "quotation" in r_data:
                        header_data = r_data["quotation"]
                    if "header" in header_data:
                        header_data = header_data["header"]

                    new_id = header_data.get('quotationId')
                    if new_id:
                        p1 = header_data.get('quoPrefix1', 'QUO')
                        p2 = header_data.get('quoPrefix2', '2026')
                        quote_number = f"{p1}-{p2}-{new_id}"
                        # Update the session with the new real quote ID
                        query['quote_id'] = quote_number
                        query['api_quotation_id'] = new_id
                        session['search_query'] = query
                        api_saved_successfully = True
                    else:
                        error_msg = "API response did not contain a valid quotation ID."
                else:
                    error_msg = f"API returned status {save_resp.status_code}: {save_resp.text}"
                    print(f"Failed to save quote via API: {save_resp.status_code} - {save_resp.text}")
        else:
            error_msg = "No cached quotation details found to save."
    except Exception as e:
        error_msg = f"Error communicating with Quotations API: {str(e)}"
        print(f"Error calling POST /api/Quotations: {e}")

    if not api_saved_successfully:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'status': 'error', 'message': error_msg}), 400
        flash(error_msg, 'danger')
        return redirect(url_for('customer.rate_results'))


    cargo_ready = query.get('cargo_ready_date')
    etd_date = None
    if cargo_ready:
        from datetime import datetime
        try:
            etd_date = datetime.strptime(cargo_ready, '%Y-%m-%d')
        except:
            pass

    booking = Booking(
        user_id=current_user.id,
        origin=origin,
        destination=destination,
        volume=float(volume) if volume else 0.0,
        selected_nvocc=nvocc_name,
        total_cost=float(total_cost) if total_cost else 0.0,
        service_type=service_type,
        api_booking_ref=quote_number,
        uuid=uuid_val,
        status='Saved Quote',
        etd=etd_date
    )
    db.session.add(booking)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'quote_number': quote_number})
        
    flash('Quote successfully saved!', 'success')
    return redirect(url_for('customer.my_quotes'))

@customer.route('/quote/<quote_id>')
@customer.route('/quote/<int:quote_id>')
@login_required
def quote_detail(quote_id):
    return redirect(url_for('customer.my_quotes'))

@customer.route('/api/quote/<path:quote_id>/breakdown')
@customer.route('/api/quote/<int:quote_id>/breakdown')
@login_required
def api_quote_breakdown(quote_id):
    if current_user.role != 'customer':
        return jsonify({'error': 'Unauthorized'}), 403
    
    ref = str(quote_id).strip()
    quote = get_booking_safely(ref, user_id=current_user.id)
    if not quote:
        quote = get_booking_safely(ref)
        
    quote_number = quote.api_booking_ref if (quote and quote.api_booking_ref) else ref
        
    breakdown = []
    currency = 'USD'
    total_cost = 0.0

    # 1. First check in-memory cache
    cache = globals().get('_GLOBAL_QUOTE_DETAILS_CACHE', {})
    det = cache.get(quote_number) or cache.get(ref)
    if det and isinstance(det, dict):
        tariff = det.get('tariff', det)
        if isinstance(tariff, dict):
            breakdown = tariff.get('lines') or []
            currency = tariff.get('quotationCurrency') or det.get('header', {}).get('currency', 'USD')
            total_cost = float(det.get('totalAmount') or det.get('header', {}).get('totalAmount') or 0.0)

    if not breakdown and quote_number:
        import requests
        headers = {'accept': 'application/json', 'x-api-key': '1'}
        customer_id = None
        if current_user.accounts:
            try: customer_id = int(current_user.accounts[0].account_id)
            except: pass
        params = {'accountId': customer_id} if customer_id else {}
        
        candidates = [quote_number]
        if quote_number.isdigit():
            candidates.extend([f"QUO-2026-{quote_number}", f"26-TDR-{quote_number}"])
            
        for cand in candidates:
            try:
                resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{cand}", params=params, headers=headers, timeout=5)
                if resp.status_code == 200:
                    resp_json = resp.json()
                    data = resp_json.get('quotation', resp_json)
                    tariff = data.get('tariff', data)
                    if isinstance(tariff, dict):
                        breakdown = tariff.get('lines') or []
                        currency = tariff.get('quotationCurrency') or data.get('header', {}).get('currency', 'USD')
                        total_cost = float(data.get('totalAmount') or data.get('header', {}).get('totalAmount') or 0.0)
                    if data:
                        cache[cand] = data
                        cache[quote_number] = data
                    break
                else:
                    print(f"API returned {resp.status_code} for {cand}: {resp.text}")
            except Exception as e:
                print(f"Error fetching breakdown for {cand}: {e}")

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
                    quo_id = header.get('quotationNo') or header.get('quoteNo') or str(header.get('quotationId') or '')
                    if quote and (str(header.get('quotationId')) in str(quote.api_booking_ref) or quote.api_booking_ref == quo_id or quote.api_booking_ref.endswith('-')):
                        tariff = data.get('tariff', data)
                        if isinstance(tariff, dict):
                            breakdown = tariff.get('lines') or []
                            currency = tariff.get('quotationCurrency') or header.get('currency', 'USD')
                    elif quote_number and (quote_number == quo_id or str(header.get('quotationId')) in quote_number):
                        tariff = data.get('tariff', data)
                        if isinstance(tariff, dict):
                            breakdown = tariff.get('lines') or []
                            currency = tariff.get('quotationCurrency') or header.get('currency', 'USD')
        except Exception:
            pass

    if breakdown and (not total_cost or total_cost <= 0):
        total_cost = sum(float(l.get('amount') or 0.0) for l in breakdown)

    return jsonify({
        'breakdown': breakdown or [],
        'total_cost': total_cost,
        'currency': currency
    })

@customer.route('/api/quote-details/<path:quote_id>')
@login_required
def api_quote_details(quote_id):
    ref = str(quote_id).strip()
    customer_id = 1
    if current_user.accounts:
        try: customer_id = int(current_user.accounts[0].account_id)
        except: pass

    import requests
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    params = {'accountId': customer_id} if customer_id else {}
    
    candidates = [ref]
    if ref.isdigit():
        candidates.extend([f"QUO-2026-{ref}", f"26-TDR-{ref}"])
        
    api_quote = None
    for cand in candidates:
        try:
            resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{cand}", params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                api_quote = resp.json().get('quotation', resp.json())
                break
        except Exception as e:
            print(f"Error fetching quote details for {cand}: {e}")

    local_booking = get_booking_safely(ref)

    if not api_quote and not local_booking:
        return jsonify({'error': 'Quote not found'}), 404

    header = api_quote.get('header', api_quote) if api_quote else {}
    routing = header.get('routing', header.get('route', {}))
    commodities = api_quote.get('commodities', []) if api_quote else []
    
    origin_loc = header.get('polLocation') or routing.get('polLocation') or (local_booking.origin if local_booking else "")
    dest_loc = header.get('podLocation') or routing.get('podLocation') or (local_booking.destination if local_booking else "")
    
    cargo = []
    if commodities:
        for c in commodities:
            cargo.append({
                'pieces': c.get('nrPackages', 1),
                'packageType': c.get('packageCode') or c.get('packageTypeDescription') or 'BX',
                'goodsType': 'HAZARDOUS' if c.get('isHazardous') else 'GENERAL',
                'weight': float(c.get('weight') or 0.0),
                'volume': float(c.get('volume') or 0.0),
                'description': c.get('commodityDescription', ''),
                'is_imo': bool(c.get('isHazardous')),
                'imo_un': c.get('imo', {}).get('un') if isinstance(c.get('imo'), dict) else '',
                'imo_class': c.get('imo', {}).get('class') if isinstance(c.get('imo'), dict) else '',
            })
    elif local_booking and local_booking.cargo_items:
        for item in local_booking.cargo_items:
            cargo.append({
                'pieces': item.quantity or 1,
                'packageType': item.package_type or 'BX',
                'goodsType': 'HAZARDOUS' if item.is_imo else 'GENERAL',
                'weight': float(item.weight_kg or 0.0),
                'volume': float(item.volume_cbm or 0.0),
                'description': item.description or '',
                'is_imo': bool(item.is_imo),
                'imo_un': item.un_number or '',
                'imo_class': item.imo_class or '',
            })



    org_country = _parse_cc(origin_loc, header.get('polCountry') or header.get('polCountryCode') or routing.get('polCountry'))
    dest_country = _parse_cc(dest_loc, header.get('podCountry') or header.get('podCountryCode') or routing.get('podCountry'))

    result = {
        'quote_ref': header.get('quoteNumber') or ref,
        'origin': origin_loc,
        'destination': dest_loc,
        'origin_country': org_country,
        'destination_country': dest_country,
        'service_type': 'LCL' if 'LCL' in str(header.get('freightTransportType') or (local_booking.service_type if local_booking else '')).upper() else 'FCL',
        'incoterm': header.get('incoTerm') or header.get('incoterm') or (local_booking.incoterm if local_booking else 'FOB'),
        'cargo_ready_date': str(header.get('validFrom') or '')[:10] or (local_booking.cargo_ready_date.strftime('%Y-%m-%d') if (local_booking and local_booking.cargo_ready_date) else ''),
        'cargo': cargo
    }

    return jsonify(result)


@customer.route('/quote/<quote_id>/email', methods=['POST'])
@login_required
def email_quote(quote_id):
    from flask import jsonify, request
    try:
        if current_user.role != 'customer':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
        data = request.get_json(silent=True) or request.form or {}
        to_email = (data.get('to') or data.get('to_email') or current_user.email or '').strip()
        cc_email = (data.get('cc') or data.get('cc_email') or '').strip()
        bcc_email = (data.get('bcc') or data.get('bcc_email') or '').strip()
        subject = (data.get('subject') or f"Your Quotation - {quote_id}").strip()
        custom_message = (data.get('message') or data.get('custom_message') or '').strip()

        if not to_email:
            return jsonify({'success': False, 'message': 'Recipient email (To) is required.'}), 400

        ref = str(quote_id).strip()
        quote = get_booking_safely(ref, user_id=current_user.id)
        if not quote:
            quote = get_booking_safely(ref)

        response = download_pdf(quote_id=quote_id)
        if response.status_code == 302:
            return jsonify({'success': False, 'message': 'Quote not found or failed to generate PDF.'})
            
        pdf_data = response.get_data()

        # Build clean custom message block if provided
        custom_msg_html = ""
        if custom_message:
            import html as html_lib
            safe_msg = html_lib.escape(custom_message).replace('\n', '<br>')
            custom_msg_html = f"""
            <div style="background-color: #f1f5f9; border-left: 4px solid #2563eb; padding: 14px 18px; margin: 20px 0; border-radius: 6px; font-size: 0.95rem; color: #1e293b; line-height: 1.5;">
                {safe_msg}
            </div>
            """

        quote_info_html = ""
        if quote:
            origin_val = getattr(quote, 'origin', '') or 'N/A'
            dest_val = getattr(quote, 'destination', '') or 'N/A'
            carrier_val = getattr(quote, 'selected_nvocc', '') or 'Standard'
            service_val = getattr(quote, 'service_type', '') or 'LCL'
            vol_val = getattr(quote, 'volume', 0) or 0
            cost_val = getattr(quote, 'total_cost', 0) or 0.0
            quote_info_html = f"""
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9rem; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569; width: 35%;">Routing:</td>
                    <td style="padding: 10px 14px; color: #0f172a; font-weight: 600;">{origin_val} &rarr; {dest_val}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Carrier / NVOCC:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{carrier_val}</td>
                </tr>
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Service Type:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{service_val}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Total Volume:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{vol_val} CBM</td>
                </tr>
                <tr style="background-color: #eff6ff;">
                    <td style="padding: 12px 14px; font-weight: bold; color: #1e40af;">Total Amount:</td>
                    <td style="padding: 12px 14px; color: #1e3a8a; font-size: 1.15rem; font-weight: 800;">${cost_val:,.2f}</td>
                </tr>
            </table>
            """

        from app.services.customer_settings import effective_settings
        settings_data = effective_settings(current_user)
        co_name = getattr(settings_data, 'company_name', None) or 'Fast Transit Line'

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 620px; margin: auto; padding: 28px; color: #1e293b; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;">
            <div style="border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px;">
                <h2 style="color: #1e3a8a; margin: 0; font-size: 1.45rem;">Quotation: {quote_id}</h2>
                <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">{co_name} · Customer Portal</div>
            </div>
            
            <p style="font-size: 1rem; margin-bottom: 12px;">Dear Valued Partner / Customer,</p>
            
            <p style="font-size: 0.95rem; line-height: 1.6; color: #334155; margin-bottom: 12px;">
                Please find below the quotation details for quotation reference <strong>{quote_id}</strong>. The complete official quotation document is attached to this email as a PDF.
            </p>

            {custom_msg_html}

            {quote_info_html}

            <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 12px 16px; margin: 20px 0; font-size: 0.88rem; color: #475569;">
                📎 <strong>Attachment:</strong> Quotation_{quote_id}.pdf (Official Quotation Document)
            </div>

            <p style="font-size: 0.92rem; color: #475569; line-height: 1.5; margin-top: 24px;">
                If you have any questions or would like to proceed with booking this shipment, please feel free to reply directly to this email or visit our portal.
            </p>

            <div style="margin-top: 28px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 0.85rem; color: #64748b;">
                <strong>Sent by:</strong> {current_user.name} ({current_user.email})<br>
                <strong>{co_name}</strong>
            </div>
        </div>
        """
        
        from app.services.email_service import SystemMailer
        success = SystemMailer.send_email(
            to_email, 
            subject, 
            html, 
            attachment_data=pdf_data, 
            attachment_filename=f"Quotation_{quote_id}.pdf",
            user=current_user,
            cc=cc_email or None,
            bcc=bcc_email or None
        )
        
        if success:
            try:
                from app.models.models import QuoteEmailDraft
                QuoteEmailDraft.query.filter_by(user_id=current_user.id, quote_ref=ref).delete()
                db.session.commit()
            except Exception:
                db.session.rollback()

            return jsonify({'success': True, 'message': f'Quote emailed successfully to {to_email}!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email. Please check your SMTP settings in Settings or contact your administrator.'})
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print("EMAIL QUOTE ERROR:", trace)
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500


@customer.route('/quote/<quote_id>/email/draft', methods=['GET', 'POST', 'DELETE'])
@login_required
def quote_email_draft(quote_id):
    from flask import jsonify, request
    from datetime import datetime
    from app.models.models import QuoteEmailDraft
    if current_user.role != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    ref = str(quote_id).strip()
    
    if request.method == 'GET':
        draft = QuoteEmailDraft.query.filter_by(user_id=current_user.id, quote_ref=ref).first()
        if draft:
            return jsonify({
                'success': True,
                'has_draft': True,
                'draft': {
                    'to': draft.to_email or '',
                    'cc': draft.cc_email or '',
                    'bcc': draft.bcc_email or '',
                    'subject': draft.subject or '',
                    'message': draft.message or '',
                    'updated_at': draft.updated_at.strftime('%Y-%m-%d %H:%M') if draft.updated_at else ''
                }
            })
        return jsonify({'success': True, 'has_draft': False, 'draft': None})

    elif request.method == 'POST':
        data = request.get_json(silent=True) or request.form or {}
        draft = QuoteEmailDraft.query.filter_by(user_id=current_user.id, quote_ref=ref).first()
        if not draft:
            draft = QuoteEmailDraft(user_id=current_user.id, quote_ref=ref)
            db.session.add(draft)
        
        draft.to_email = (data.get('to') or '').strip()
        draft.cc_email = (data.get('cc') or '').strip()
        draft.bcc_email = (data.get('bcc') or '').strip()
        draft.subject = (data.get('subject') or '').strip()
        draft.message = (data.get('message') or '').strip()
        draft.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': 'Draft saved successfully!'})

    elif request.method == 'DELETE':
        QuoteEmailDraft.query.filter_by(user_id=current_user.id, quote_ref=ref).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Draft deleted successfully.'})


@customer.route('/quote/<quote_id>/download_pdf')
@customer.route('/quote/<int:quote_id>/download_pdf')
@customer.route('/download_pdf')
@login_required
def download_pdf(quote_id=None):
    if current_user.role != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    if not quote_id:
        quote_id = request.args.get('quote_id')
        
    ref = str(quote_id or '').strip()
    quote = get_booking_safely(ref, user_id=current_user.id)
    if not quote:
        quote = get_booking_safely(ref)
    if not quote:
        flash('Quote not found.', 'danger')
        return redirect(url_for('customer.my_quotes'))
    
    breakdown = []
    header = {}
    commodities = []
    sailings = []
    tariff = {}

    quote_number = quote.api_booking_ref or ref
    if quote_number:
        import requests
        headers = {'accept': 'application/json', 'x-api-key': '1'}
        customer_id = None
        if current_user.accounts:
            try: customer_id = int(current_user.accounts[0].account_id)
            except: pass
        if not customer_id and hasattr(quote, 'account_id') and quote.account_id:
            try: customer_id = int(quote.account_id)
            except: pass
        if not customer_id and hasattr(quote, 'customer_id') and quote.customer_id:
            try: customer_id = int(quote.customer_id)
            except: pass
        params = {'accountId': customer_id} if customer_id else {}
        
        candidates = [quote_number]
        if quote_number.isdigit():
            candidates.extend([f"QUO-2026-{quote_number}", f"26-TDR-{quote_number}"])
            
        for cand in candidates:
            try:
                resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{cand}", params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    resp_json = resp.json()
                    data = resp_json.get('quotation', resp_json)
                    header = data.get('header', {})
                    commodities = data.get('commodities', [])
                    sailings = data.get('sailings', [])
                    tariff = data.get('tariff', data)
                    if isinstance(tariff, dict):
                        breakdown = tariff.get('lines') or []
                    break
                else:
                    print(f"API returned {resp.status_code} for {cand}: {resp.text}")
            except Exception as e:
                print(f"Failed to fetch quote breakdown for {cand}:", e)

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
                    header = data.get('header', {})
                    commodities = data.get('commodities', [])
                    sailings = data.get('sailings', [])
                    tariff = data.get('tariff', data)
                    if isinstance(tariff, dict):
                        breakdown = tariff.get('lines') or []
        except Exception as e:
            pass

    # --- PDF Formatting Helpers ---
    def fmt_num(val, decimals=2):
        if val is None or val == '':
            return ''
        try:
            f = float(val)
        except (ValueError, TypeError):
            return str(val)
        return f"{f:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def fmt_date(val, leading_zero=True):
        if not val:
            return ''
        val_str = str(val).strip()
        import re
        m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', val_str)
        if m:
            y, m, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return f"{d:02d}/{m:02d}/{y}" if leading_zero else f"{d}/{m}/{y}"
        m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})', val_str)
        if m:
            d, m, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return f"{d:02d}/{m:02d}/{y}" if leading_zero else f"{d}/{m}/{y}"
        if hasattr(val, 'day'):
            return f"{val.day:02d}/{val.month:02d}/{val.year}" if leading_zero else f"{val.day}/{val.month}/{val.year}"
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

    # Register filters on jinja environment
    current_app.jinja_env.filters['fmt_num'] = fmt_num
    current_app.jinja_env.filters['fmt_date'] = fmt_date
    current_app.jinja_env.filters['clean_location'] = clean_location
    current_app.jinja_env.filters['truncate_str'] = truncate_str

    # Windows file locking monkeypatch for xhtml2pdf font embedding
    import tempfile, os
    import xhtml2pdf.files as xf
    if not getattr(xf.BaseFile, '_is_win_patched', False):
        def _monkey_get_named_tmp_file(self):
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
        xf.BaseFile.get_named_tmp_file = _monkey_get_named_tmp_file
        xf.BaseFile._is_win_patched = True

    def _pisa_link_callback(uri, rel):
        if uri.startswith('font:'):
            font_name = uri.split(':', 1)[1].lower()
            font_map = {
                'arial': r'C:\Windows\Fonts\arial.ttf',
                'arial-bold': r'C:\Windows\Fonts\arialbd.ttf',
                'tahoma': r'C:\Windows\Fonts\tahoma.ttf',
                'tahoma-bold': r'C:\Windows\Fonts\tahomabd.ttf',
                'times': r'C:\Windows\Fonts\times.ttf',
            }
            return font_map.get(font_name, uri)
        return uri

    quotation_currency = (tariff.get('quotationCurrency') if isinstance(tariff, dict) else None) or header.get('currency') or getattr(quote, 'currency', None) or 'USD'
    quotation_currency = quotation_currency.strip().upper()

    # Extract dynamic Rate of Exchange (ROE) and target currency from API payload
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
        for l in breakdown:
            r = float(l.get('exchangeRate') or 0.0)
            if r > 0:
                exchange_rate_val = r
                break

    if not exchange_rate_val:
        exchange_rate_val = 2.0  # default fallback

    # Total packages, weight, volume
    total_packages = sum(int(c.get('nrPackages') or 1) for c in commodities) if commodities else (getattr(quote, 'packages', None) or 1)
    total_weight = sum(float(c.get('weight') or 0.0) for c in commodities) if commodities else float(getattr(quote, 'weight', None) or 0.0)
    if total_weight == 0.0 and getattr(quote, 'weight', None):
        try: total_weight = float(quote.weight)
        except: pass
    total_volume = sum(float(c.get('volume') or 0.0) for c in commodities) if commodities else float(getattr(quote, 'volume', None) or 0.0)
    if total_volume == 0.0 and getattr(quote, 'volume', None):
        try: total_volume = float(quote.volume)
        except: pass

    if commodities:
        if float(commodities[0].get('weight') or 0.0) == 0.0 and total_weight > 0.0:
            commodities[0]['weight'] = total_weight
        if float(commodities[0].get('volume') or 0.0) == 0.0 and total_volume > 0.0:
            commodities[0]['volume'] = total_volume

    # Tariff currency grouping & calculations
    groups_map = {}
    for item in breakdown:
        c = (item.get('currency') or quotation_currency).strip().upper()
        if c not in groups_map:
            groups_map[c] = []
        
        aname = (item.get('articleName') or '').strip()
        cg = (item.get('articleCostGroup') or '').strip().upper()
        calc = (item.get('calcCode') or item.get('calcCodeBase') or '').strip().upper()
        calc_code_display = 'W/M' if calc in ['MTQ', 'KGM', 'W/M'] else 'LUMPSUM'
        
        raw_qty = item.get('appliedQty')
        if raw_qty is not None and float(raw_qty) > 0:
            qty_val = float(raw_qty)
        else:
            chargeable = max(total_weight / 1000.0, total_volume)
            qty_val = chargeable if calc_code_display == 'W/M' and chargeable > 0 else 1.0
            
        rate_val = float(item.get('appliedRate') if item.get('appliedRate') is not None else (item.get('price') or item.get('amount') or 0.0))
        min_val = None
        if item.get('minimum') is not None:
            try: min_val = float(item['minimum'])
            except: min_val = None
        elif calc_code_display == 'LUMPSUM':
            min_val = rate_val
        elif calc_code_display == 'W/M':
            if 'OCEAN FREIGHT' in aname.upper():
                min_val = 12.0
            elif any(k in aname.upper() for k in ['EMERGENCY', 'CONGESTION', 'ECS']):
                min_val = None
            else:
                min_val = rate_val
                
        amt_val = float(item.get('amount') if item.get('amount') is not None else (rate_val * qty_val))
        
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

    # Order currency groups: other currencies first (e.g. EUR), quotation currency last (e.g. USD)
    all_currs = list(groups_map.keys())
    sorted_currs = [c for c in all_currs if c != quotation_currency] + ([quotation_currency] if quotation_currency in all_currs else [])

    currency_groups = []
    grand_total = 0.0

    for c in sorted_currs:
        lines = groups_map[c]
        if c == quotation_currency:
            # Place Ocean Freight lines FIRST in the quotation currency group
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

    if not grand_total and getattr(quote, 'total_cost', None):
        grand_total = float(quote.total_cost)

    # Rate of Exchange string: base converted currency = 1, quotation currency = rate (e.g. EUR = 1, USD = 2,00)
    source_curr = sorted_currs[0] if (sorted_currs and sorted_currs[0] != quotation_currency) else (from_curr if from_curr != quotation_currency else 'EUR')
    roe_text = f"{source_curr} = 1, {quotation_currency} = {fmt_num(exchange_rate_val, 2)}"

    from app import get_cached_system_settings
    settings_data = get_cached_system_settings(current_user)
    
    # Check for client PDF logo
    logo_abs_path = os.path.join(current_app.root_path, 'static', 'img', 'ftl_pdf_logo.png')
    if not os.path.exists(logo_abs_path):
        logo_rel = settings_data.get('logo_path', 'img/logo.png')
        logo_abs_path = os.path.join(current_app.root_path, 'static', logo_rel)
    if not os.path.exists(logo_abs_path):
        logo_abs_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')

    sys_company_name = settings_data.get('company_name', 'FAST TRANSIT LINE')
    raw_company_phone = settings_data.get('company_phone') or '+32 (0)3 5419676'
    company_address_raw = settings_data.get('company_address', 'SCHOUWKENSSTRAAT 1\n2030 ANTWERPEN\nBELGIUM')
    address_lines = [l.strip() for l in company_address_raw.replace('\r', '').split('\n') if l.strip()]
    if len(address_lines) == 1 and ',' in address_lines[0]:
        address_lines = [l.strip() for l in address_lines[0].split(',') if l.strip()]

    phone_line = raw_company_phone if raw_company_phone.upper().startswith('PHONE:') else f"PHONE: {raw_company_phone}"
    full_address_lines = [sys_company_name]
    for al in address_lines:
        if al.upper() != sys_company_name.upper() and not al.upper().startswith('PHONE:'):
            full_address_lines.append(al)
    full_address_lines.append(phone_line)

    company_name = (header.get('customerName') or header.get('companyName') or 
                    (current_user.company.name if (hasattr(current_user, 'company') and current_user.company) else None) or 
                    (getattr(current_user.accounts[0], 'account_name', None) if current_user.accounts else None) or 
                    getattr(current_user, 'name', 'Valued Customer'))

    prepared_by_name = (header.get('preparedBy') or header.get('salesPerson') or header.get('createdBy') or '')
    prepared_by_email = (header.get('salesPersonEmail') or header.get('createdByEmail') or '')
    prepared_by_phone = (header.get('salesPersonPhone') or header.get('createdByPhone') or '')

    routing_data = header.get('routing', {}) if isinstance(header, dict) else {}
    por_location = clean_location(routing_data.get('porLocation') or getattr(quote, 'origin', '') or header.get('polLocation') or '')
    pol_location = clean_location(routing_data.get('polLocation') or getattr(quote, 'origin', '') or '')
    pod_location = clean_location(routing_data.get('podLocation') or getattr(quote, 'destination', '') or '')
    del_location = clean_location(routing_data.get('delLocation') or getattr(quote, 'destination', '') or '')

    destination_clean = clean_location(getattr(quote, 'destination', '') or header.get('podLocation') or '')
    pol_clean = clean_location(getattr(quote, 'origin', '') or header.get('polLocation') or '')
    destination_remarks = header.get('destinationRemarks') or ''

    print_date = fmt_date(header.get('validFrom') or header.get('createdOn') or getattr(quote, 'created_at', None), leading_zero=False)
    valid_from_formatted = fmt_date(header.get('validFrom') or getattr(quote, 'created_at', None), leading_zero=True)
    valid_until_formatted = fmt_date(header.get('validUntil') or getattr(quote, 'valid_until', None) or header.get('validFrom'), leading_zero=True)

    haz_un = header.get('unNumber') or ''
    haz_class = header.get('hazardClass') or ''
    haz_pg = header.get('packingGroup') or ''
    if not haz_un and commodities:
        haz_un = commodities[0].get('unNumber') or commodities[0].get('un') or ''
        haz_class = commodities[0].get('imdgClass') or commodities[0].get('hazardClass') or ''
        haz_pg = commodities[0].get('packingGroup') or commodities[0].get('pg') or ''

    pickup_remarks = header.get('pickupRemarks') or header.get('pickup_remarks') or 'Please note that the free time for pick up is limited to 30 Minutes.'
    inco_term = (header.get('incoTerm') or header.get('incoterm') or getattr(quote, 'incoterm', None) or 'CFR').strip().upper()

    final_quote_num = header.get('quoteNumber') or getattr(quote, 'api_booking_ref', None) or (f"QUO-{quote.id}" if hasattr(quote, 'id') else ref)

    # Use ReportLab Quotation PDF Generator for pixel-perfect client replication
    from app.quotation_pdf import generate_quotation_pdf
    from flask import make_response

    payload = {
        'quote_number': final_quote_num,
        'print_date': print_date,
        'to_company': company_name,
        'attn_name': header.get('contactName') or getattr(current_user, 'name', ''),
        'from_name': prepared_by_name,
        'from_email': prepared_by_email,
        'from_phone': prepared_by_phone,
        'logo_path': logo_abs_path,
        'company_name': sys_company_name,
        'company_address_lines': full_address_lines,
        'company_phone': raw_company_phone,
        'inco_term': inco_term,
        'por_location': por_location,
        'pol_location': pol_location,
        'pod_location': pod_location,
        'del_location': del_location,
        'commodities': commodities,
        'total_packages': total_packages,
        'total_weight': total_weight,
        'total_volume': total_volume,
        'haz_un': haz_un,
        'haz_class': haz_class,
        'haz_pg': haz_pg,
        'currency_groups': currency_groups,
        'quotation_currency': quotation_currency,
        'grand_total': grand_total,
        'roe_text': roe_text,
        'valid_from_formatted': valid_from_formatted,
        'valid_until_formatted': valid_until_formatted,
        'pickup_remarks': pickup_remarks,
        'destination_clean': destination_clean,
        'sailings': sailings
    }

    try:
        pdf_bytes = generate_quotation_pdf(payload)
    except Exception as e:
        current_app.logger.error(f"Failed to generate ReportLab quotation PDF: {e}", exc_info=True)
        flash('Failed to generate PDF document.', 'danger')
        return redirect(url_for('customer.my_quotes'))

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Quotation_{final_quote_num}.pdf'
    
    return response

@customer.route('/rates', methods=['GET', 'POST'])
@login_required
def rates():
    if current_user.role != 'customer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        import requests
        
        service_type = request.form.get('service_type', 'LCL').upper()
        goods_types = [g.strip().upper() for g in request.form.getlist('goods_type[]')]
        
        # Extract IDs from User Profile mappings
        branch_id = 1
        customer_id = 1
        account_contact_id = current_user.erp_contact_id or current_user.id
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
        # Extract locodes and clean names from origin and destination
        origin_str = request.form.get("origin", "")
        dest_str = request.form.get("destination", "")
        origin_name, pol_locode = parse_location(origin_str)
        dest_name, pod_locode = parse_location(dest_str)

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

        incoterm_val = request.form.get("freight_terms", "").strip()
        if not incoterm_val:
            flash("Incoterm is required. Please select an Incoterm before submitting.", "danger")
            return redirect(url_for('customer.rates'))

        vas_list = request.form.getlist('vas_code[]')

        payload = {
            "branchId": branch_id,
            "customerId": customer_id,
            "accountContactId": account_contact_id,
            "customerReference": request.form.get("customer_reference") or "",
            "trafficType": traffic_type,
            "freightTransportMode": mapped_mode,
            "freightTransportType": mapped_svc,
            "movementType": mapped_mov,
            "cargoClassification": "1",
            "incoterm": incoterm_val,
            "validOn": valid_from,
            "currency": request.form.get("currency", "USD"),
            "paymentMethod": "NS", # API currently only supports 'NS' and throws 500 on prepaid/collect
            "specialInstructions": request.form.get("special_instructions", ""),
            "route": {
                "porLocode": pol_locode,
                "porLocation": origin_name,
                "polLocode": pol_locode,
                "polLocation": origin_name,
                "podLocode": pod_locode,
                "podLocation": dest_name,
                "delLocode": pod_locode,
                "delLocation": dest_name,
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
                    "isHazardous": is_haz,
                    "imo": {
                        "un": item_imo_uns[i] if (is_haz and i < len(item_imo_uns) and item_imo_uns[i]) else "string", 
                        "class": item_imo_classes[i] if (is_haz and i < len(item_imo_classes) and item_imo_classes[i]) else "string", 
                        "properShippingName": item_imo_names[i] if (is_haz and i < len(item_imo_names) and item_imo_names[i]) else "string", 
                        "packingGroup": item_imo_groups[i] if (is_haz and i < len(item_imo_groups) and item_imo_groups[i]) else "string"
                    }
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
                    "isHazardous": is_haz,
                    "imo": {
                        "un": "string", "class": "string", "properShippingName": "string", "packingGroup": "string"
                    }
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
                
                # Option 1 Validation: Check if Customs Clearance was requested and verify tariff lines
                customs_requested = False
                for key in request.form.keys():
                    if any(k in key.lower() for k in ['custom', 'clearance', 'service1']):
                        val = str(request.form.get(key, '')).lower()
                        if val in ['on', 'true', '1', 'yes'] or any(k in val for k in ['custom', 'clearance']):
                            customs_requested = True
                            break
                for vas in vas_list:
                    if any(k in str(vas).lower() for k in ['custom', 'clearance']):
                        customs_requested = True
                        break

                quot_obj = data.get("quotation", data)
                tariff_lines = quot_obj.get("tariff", {}).get("lines", [])
                has_customs_charge = any(
                    any(term in (line.get('articleName') or '').upper() or term in (line.get('articleCode') or '').upper() for term in ['CUSTOM', 'CLEARANCE', 'DECLARATION', 'CUST'])
                    for line in tariff_lines
                )

                if customs_requested and not has_customs_charge:
                    flash("Quotation Unavailable: You requested Customs Clearance, but the ERP tariff database for this lane does not have a configured Customs Clearance charge. Incomplete offers with missing charges cannot be generated.", "danger")
                    return redirect(url_for('customer.rates'))


                # The new API endpoint wraps the response in a "quotation" object containing "header"
                if "quotation" in data and "header" in data["quotation"]:
                    header_data = data["quotation"]["header"]
                else:
                    header_data = data
                    
                quo_id = header_data.get('quotationNo') or header_data.get('quoteNo') or str(header_data.get('quotationId') or '')
                flash(f"Success! Quotation {quo_id} has been created.", "success")
                
                # Save complete search query into session for Modify Search feature
                session['search_query'] = {
                    'origin': origin_str,
                    'destination': dest_str,
                    'volume': sum(c.get('volume', 0) for c in payload['cargo']),
                    'service_type': service_type,
                    'transport_mode': request.form.get('transport_mode', 'ocean').lower(),
                    'movement_type': request.form.get('movement_type', 'PORT_TO_PORT'),
                    'cargo_items': payload['cargo'],
                    'cargo_ready_date': valid_from,
                    'traffic_type': traffic_type,
                    'incoterm': incoterm_val,
                    'freight_terms': request.form.get('payment_terms') or request.form.get('freight_terms') or '',
                    'customer_reference': request.form.get('customer_reference') or '',
                    'special_instructions': request.form.get('special_instructions') or '',
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
                
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'quote_id': quo_id,
                        'quotation': data
                    })

                return redirect(url_for('customer.rate_results'))
            else:
                print("Constructed Payload:", json.dumps(payload, indent=2))
                print("API ERROR:", api_resp.status_code, api_resp.text)
                
                # Parse the error message if possible
                error_msg = api_resp.text
                try:
                    err_json = api_resp.json()
                    error_msg = err_json.get('message', err_json.get('error', api_resp.text))
                except Exception:
                    pass
                
                if request.is_json:
                    return jsonify({'success': False, 'message': f"Failed to create quotation: {error_msg}"}), 400

                flash(f"Failed to create quotation: {error_msg}", "danger")
                return redirect(url_for('customer.rates'))
        except Exception as e:
            flash(f"API Error: {str(e)}", "danger")
            return redirect(url_for('customer.rates'))
    query_data = {}
    quote_id = request.args.get('quote_id')
    origin_param = request.args.get('origin')
    dest_param = request.args.get('destination')
    modify_param = request.args.get('modify')

    if quote_id:
        quote = get_booking_safely(quote_id, user_id=current_user.id)
        if not quote:
            quote = get_booking_safely(quote_id)
        if quote:
            cargo_items = []
            if quote.cargo_items:
                for item in quote.cargo_items:
                    imo_un = getattr(item, 'un_number', '') or getattr(item, 'imo_un', '') or ''
                    imo_class = getattr(item, 'imo_class', '') or ''
                    if imo_un == 'string': imo_un = ''
                    if imo_class == 'string': imo_class = ''
                    is_haz = getattr(item, 'is_imo', False) or getattr(item, 'is_hazardous', False) or bool(imo_un)
                    cargo_items.append({
                        'pieces': getattr(item, 'quantity', 1) or getattr(item, 'pieces', 1) or 1,
                        'type': getattr(item, 'package_type', 'PX') or 'PX',
                        'length': getattr(item, 'length', '') or '',
                        'width': getattr(item, 'width', '') or '',
                        'height': getattr(item, 'height', '') or '',
                        'weight': getattr(item, 'weight_kg', '') or getattr(item, 'weight', '') or '',
                        'volume': getattr(item, 'volume_cbm', '') or getattr(item, 'volume', '') or '',
                        'desc': getattr(item, 'general_description', None) or getattr(item, 'description', None) or 'General Cargo',
                        'goods_type': 'hazardous' if is_haz else 'commercial',
                        'imo_un': imo_un,
                        'imo_class': imo_class
                    })
            if not cargo_items:
                # Fallback if no individual items exist
                cargo_items.append({
                    'pieces': getattr(quote, 'pieces', getattr(quote, 'quantity', 1)) or 1,
                    'type': 'PX',
                    'length': '', 'width': '', 'height': '',
                    'weight': getattr(quote, 'weight', getattr(quote, 'total_weight', 0)),
                    'volume': getattr(quote, 'volume', getattr(quote, 'total_volume', 0)),
                    'desc': 'General Cargo',
                    'goods_type': 'commercial',
                    'imo_un': '', 'imo_class': ''
                })
            org_country = _parse_cc(quote.origin, None)
            dest_country = _parse_cc(quote.destination, None)
            query_data = {
                'origin': quote.origin or '',
                'destination': quote.destination or '',
                'origin_type': 'port',
                'dest_type': 'port',
                'origin_country': org_country,
                'dest_country': dest_country,
                'service': quote.service_type or 'LCL',
                'transport_mode': getattr(quote, 'transport_mode', 'ocean') or 'ocean',
                'movement_type': getattr(quote, 'movement_type', 'PORT_TO_PORT') or 'PORT_TO_PORT',
                'traffic_type': getattr(quote, 'traffic_type', 'EX') or 'EX',
                'incoterm': getattr(quote, 'incoterm', '') or '',
                'freight_terms': getattr(quote, 'freight_terms', '') or '',
                'cargo_ready_date': quote.created_at.strftime('%Y-%m-%d') if quote.created_at else '',
                'cargoItems': cargo_items,
                'totalVolume': quote.volume or 0,
                'quote_id': quote.api_booking_ref or quote.id
            }

        if not query_data:
            quote_number = str(quote_id).strip()
            headers = {'accept': 'application/json', 'x-api-key': '1'}
            customer_id = None
            if hasattr(current_user, 'accounts') and current_user.accounts:
                try: customer_id = int(current_user.accounts[0].account_id)
                except: pass
            params = {'accountId': customer_id} if customer_id else {}
            
            candidates = [quote_number]
            if quote_number.isdigit():
                candidates.extend([f"QUO-2026-{quote_number}", f"26-TDR-{quote_number}"])
                
            header = {}
            commodities = []
            for cand in candidates:
                try:
                    resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{cand}", params=params, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        resp_json = resp.json()
                        data = resp_json.get('quotation', resp_json)
                        header = data.get('header', {})
                        commodities = data.get('commodities') or data.get('freightDetails') or data.get('freight_details') or []
                        break
                except Exception as e:
                    print(f"Failed to fetch quotation for rerun {cand}:", e)
            
            if header or commodities:
                routing = header.get('routing', {}) if isinstance(header, dict) else {}
                pol_name = routing.get('polLocation') or routing.get('porLocation') or header.get('polLocation') or ''
                pod_name = routing.get('podLocation') or routing.get('delLocation') or header.get('podLocation') or ''
                pol_code = routing.get('polLocode') or routing.get('porLocode') or ''
                pod_code = routing.get('podLocode') or routing.get('delLocode') or ''
                
                pol_full = f"{pol_name} ({pol_code})" if pol_code and '(' not in pol_name else pol_name
                pod_full = f"{pod_name} ({pod_code})" if pod_code and '(' not in pod_name else pod_name
                
                cargo_items = []
                for c in commodities:
                    dims = c.get('dimensions', {}) if isinstance(c.get('dimensions'), dict) else {}
                    imo = c.get('imo', {}) if isinstance(c.get('imo'), dict) else {}
                    imo_un = imo.get('un') or c.get('imo_un') or c.get('un_number') or ''
                    imo_class = imo.get('class') or c.get('imo_class') or ''
                    if imo_un == 'string': imo_un = ''
                    if imo_class == 'string': imo_class = ''
                    is_haz = c.get('isHazardous') or bool(imo_un)
                    
                    cargo_items.append({
                        'pieces': c.get('nrPackages') or c.get('pieceCount') or c.get('quantity') or 1,
                        'type': c.get('packageCode') or c.get('packageTypeDescription') or 'PX',
                        'length': dims.get('length') or c.get('length') or '',
                        'width': dims.get('width') or c.get('width') or '',
                        'height': dims.get('height') or c.get('height') or '',
                        'weight': c.get('weight') or '',
                        'volume': c.get('volume') or '',
                        'desc': c.get('commodityDescription') or c.get('desc') or 'General Cargo',
                        'goods_type': 'hazardous' if is_haz else 'commercial',
                        'imo_un': imo_un,
                        'imo_class': imo_class
                    })
                if not cargo_items:
                    cargo_items.append({
                        'pieces': header.get('totalPackages') or header.get('totalPieces') or 1,
                        'type': 'PX',
                        'length': '', 'width': '', 'height': '',
                        'weight': header.get('totalWeight') or header.get('weight') or '',
                        'volume': header.get('totalVolume') or header.get('volume') or '',
                        'desc': 'General Cargo',
                        'goods_type': 'commercial',
                        'imo_un': '', 'imo_class': ''
                    })

                org_country = _parse_cc(pol_full, None)
                dest_country = _parse_cc(pod_full, None)
                pm = header.get('paymentMethod', '')
                f_terms = 'prepaid' if pm == 'PP' else ('collect' if pm == 'CC' else '')
                
                query_data = {
                    'origin': pol_full,
                    'destination': pod_full,
                    'origin_type': 'port',
                    'dest_type': 'port',
                    'origin_country': org_country,
                    'dest_country': dest_country,
                    'service': 'FCL' if header.get('freightTransportType') == 'FCL' else 'LCL',
                    'transport_mode': 'air' if str(header.get('freightTransportMode')) == '20' else 'ocean',
                    'movement_type': 'PORT_TO_PORT',
                    'traffic_type': header.get('trafficType') or 'EX',
                    'incoterm': header.get('incoTerm') or 'CFR',
                    'freight_terms': f_terms,
                    'cargo_ready_date': (header.get('validFrom') or '')[:10],
                    'cargoItems': cargo_items,
                    'totalVolume': sum(float(c.get('volume') or 0) for c in commodities if c.get('volume')),
                    'quote_id': quote_number
                }

        if query_data:
            session['search_query'] = query_data
    elif origin_param or dest_param:
        org_country = _parse_cc(origin_param, None) if origin_param else ''
        dest_country = _parse_cc(dest_param, None) if dest_param else ''
        query_data = {
            'origin': origin_param or '',
            'destination': dest_param or '',
            'origin_type': 'port',
            'dest_type': 'port',
            'origin_country': org_country,
            'dest_country': dest_country,
            'service': request.args.get('service', 'LCL')
        }
    elif modify_param == '1':
        sq = session.get('search_query') or {}
        if sq:
            org_country = _parse_cc(sq.get('origin'), None) if sq.get('origin') else ''
            dest_country = _parse_cc(sq.get('destination'), None) if sq.get('destination') else ''
            
            c_items = []
            if sq.get('cargo_items'):
                for ci in sq.get('cargo_items'):
                    dims = ci.get('dimensions', {}) if isinstance(ci.get('dimensions'), dict) else {}
                    imo = ci.get('imo', {}) if isinstance(ci.get('imo'), dict) else {}
                    # Filter out 'string' API placeholder values from IMO fields
                    imo_un = imo.get('un') or ci.get('imo_un') or ci.get('un_number') or ''
                    imo_class = imo.get('class') or ci.get('imo_class') or ''
                    if imo_un == 'string': imo_un = ''
                    if imo_class == 'string': imo_class = ''
                    is_haz = ci.get('isHazardous') or ci.get('is_imo') or bool(imo_un)
                    c_items.append({
                        'pieces': ci.get('pieceCount') or ci.get('pieces') or ci.get('quantity') or ci.get('nrPackages') or 1,
                        'type': ci.get('packageType') or ci.get('type') or ci.get('packageCode') or 'PX',
                        'length': dims.get('length') or ci.get('length') or '',
                        'width': dims.get('width') or ci.get('width') or '',
                        'height': dims.get('height') or ci.get('height') or '',
                        'weight': ci.get('weight') or ci.get('weight_kg') or '',
                        'volume': ci.get('volume') or ci.get('volume_cbm') or '',
                        'desc': ci.get('commodityDescription') or ci.get('desc') or ci.get('description') or 'General Cargo',
                        'goods_type': 'hazardous' if is_haz else 'commercial',
                        'imo_un': imo_un,
                        'imo_class': imo_class
                    })


            query_data = {
                'origin': sq.get('origin') or '',
                'destination': sq.get('destination') or '',
                'origin_type': 'port',
                'dest_type': 'port',
                'origin_country': org_country,
                'dest_country': dest_country,
                'service': sq.get('service_type') or 'LCL',
                'transport_mode': sq.get('transport_mode') or 'ocean',
                'movement_type': sq.get('movement_type') or 'PORT_TO_PORT',
                'cargo_ready_date': sq.get('cargo_ready_date') or '',
                'cargoItems': c_items,
                'totalVolume': sq.get('volume') or 0,
                'traffic_type': sq.get('traffic_type') or 'EX',
                'incoterm': sq.get('incoterm') or '',
                'freight_terms': sq.get('freight_terms') or '',
                'customer_reference': sq.get('customer_reference') or '',
                'special_instructions': sq.get('special_instructions') or ''
            }

    freight_terms = [{'code': 'prepaid', 'name': 'Prepaid'}, {'code': 'collect', 'name': 'Collect'}]
    
    from app.services.customer_settings import effective_settings
    sys_settings = effective_settings(current_user)
    import json
    incoterm_rules_json = json.dumps(sys_settings.incoterm_rules) if sys_settings and sys_settings.incoterm_rules else 'null'

    return render_template('customer/rates.html',
                         countries=[],
                         incoterms=[],
                         package_types_json='[]',
                         container_types_json='[]',
                         vas_types_json='[]',
                         weight_uom_json='[]',
                         volume_uom_json='[]',
                         freight_terms=freight_terms,
                         query=query_data,
                         incoterm_rules_json=incoterm_rules_json)

@customer.route('/api/lookups')
@login_required
def api_lookups():
    from app.services.master_data import get_code_list
    
    # 1. Fetch Countries
    try:
        countries_api = get_code_list('countrycode')
        countries = [c.to_dict() for c in countries_api] if countries_api else []
    except Exception as ex:
        print("Error fetching countries:", ex)
        countries = []

    # 2. Fetch other lookup fields
    try:
        incoterms_api = get_code_list('incoterm')
        incoterms = [i.to_dict() for i in incoterms_api] if incoterms_api else []
        
        package_api = get_code_list('packagecode')
        package_types = [pt.to_dict() for pt in package_api] if package_api else [
            {'code': 'PX', 'name': 'Pallet'},
            {'code': 'BX', 'name': 'Box'},
            {'code': 'CR', 'name': 'Crate'},
            {'code': 'DR', 'name': 'Drum'},
            {'code': 'BG', 'name': 'Bag'},
            {'code': 'ZR', 'name': 'IBC'}
        ]
        
        container_api = get_code_list('freighttransporttype')
        container_types = [ct.to_dict() for ct in container_api] if container_api else []
        
        vas_api = get_code_list('vastype')
        vas_types = [c.to_dict() for c in vas_api] if vas_api else []

        weight_uom = [{'code': 'kg', 'name': 'Kilograms (kg)'}, {'code': 'lbs', 'name': 'Pounds (lbs)'}]
        volume_uom = [{'code': 'cbm', 'name': 'Cubic Meters (cbm)'}, {'code': 'cbf', 'name': 'Cubic Feet (cbf)'}]
    except Exception as ex:
        print("Error fetching lookup lists:", ex)
        incoterms = []
        package_types = [
            {'code': 'PX', 'name': 'Pallet'},
            {'code': 'BX', 'name': 'Box'},
            {'code': 'CR', 'name': 'Crate'},
            {'code': 'DR', 'name': 'Drum'},
            {'code': 'BG', 'name': 'Bag'},
            {'code': 'ZR', 'name': 'IBC'}
        ]
        container_types = []
        vas_types = []
        weight_uom = [{'code': 'kg', 'name': 'Kilograms (kg)'}, {'code': 'lbs', 'name': 'Pounds (lbs)'}]
        volume_uom = [{'code': 'cbm', 'name': 'Cubic Meters (cbm)'}, {'code': 'cbf', 'name': 'Cubic Feet (cbf)'}]

    return jsonify({
        'countries': countries,
        'incoterms': incoterms,
        'package_types': package_types,
        'container_types': container_types,
        'vas_types': vas_types,
        'weight_uom': weight_uom,
        'volume_uom': volume_uom
    })


@customer.route('/api/get-ports/<direction>')
@customer.route('/api/get-ports/<direction>/<country_code>')
@login_required
def api_get_ports(direction, country_code=None):
    import requests
    headers = {'accept': '*/*', 'x-api-key': '1'}
    endpoint = 'OriginPorts' if direction.lower() == 'origin' else 'DestinationPorts'
    
    # If no country_code or 'all', fetch all ports
    if not country_code or country_code.lower() == 'all':
        url = f"http://realnexus.comit.cloud:5000/api/Ports/{endpoint}"
    else:
        url = f"http://realnexus.comit.cloud:5000/api/Ports/{endpoint}/{country_code}"
        
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            ports = resp.json()
            valid_ports = []
            for p in ports:
                if p.get('isActive') and p.get('code'):
                    # The API might not return countryName directly, but it returns 'country'
                    c_code = p.get('country', country_code.upper() if country_code and country_code.lower() != 'all' else '')
                    valid_ports.append({
                        'code': p['code'],
                        'name': p.get('name', p['code']),
                        'country': c_code
                    })
            return jsonify(valid_ports)
        return jsonify([])
    except Exception as e:
        print(f"Error fetching ports for {country_code}: {e}")
    return jsonify([])


# In-memory cache for RealNexus transport lanes
_TRANSPORT_LANES_CACHE = {
    'timestamp': 0,
    'lanes': []
}

def _get_cached_transport_lanes():
    """Fetch and cache all Transport Lanes from Realnexus ERP (cache TTL: 1 hour)."""
    now = time.time()
    if _TRANSPORT_LANES_CACHE['lanes'] and (now - _TRANSPORT_LANES_CACHE['timestamp'] < 3600):
        return _TRANSPORT_LANES_CACHE['lanes']
    
    headers = {'accept': '*/*', 'x-api-key': '1'}
    tl_url = 'http://realnexus.comit.cloud:5000/api/Ports/TransportLanes'
    try:
        resp = requests.get(tl_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            lanes = resp.json()
            if isinstance(lanes, list) and len(lanes) > 0:
                _TRANSPORT_LANES_CACHE['lanes'] = lanes
                _TRANSPORT_LANES_CACHE['timestamp'] = now
                return lanes
    except Exception as e:
        print("Warning: Failed to fetch transport lanes from API:", e)
        
    return _TRANSPORT_LANES_CACHE['lanes']

def _extract_locode(val):
    if not val:
        return ''
    val_str = str(val).strip()
    match = re.search(r'\(([A-Za-z0-9]{5})\)', val_str)
    if match:
        return match.group(1).upper()
    cleaned = val_str.upper()
    if len(cleaned) == 5 and ' ' not in cleaned:
        return cleaned
    return cleaned

@customer.route('/api/detect-traffic-type')
@login_required
def api_detect_traffic_type():
    origin_raw = request.args.get('origin', '')
    dest_raw = request.args.get('destination', '')
    
    origin = _extract_locode(origin_raw)
    destination = _extract_locode(dest_raw)
    
    if not origin or not destination:
        return jsonify({
            'success': False,
            'message': 'Both origin and destination codes are required.'
        }), 400
        
    branch_id = None
    if request.args.get('branchId'):
        try: branch_id = int(request.args.get('branchId'))
        except: pass
    if not branch_id and current_user.branches:
        try: branch_id = int(current_user.branches[0].branch_id)
        except: pass
        
    lanes = _get_cached_transport_lanes()
    
    # Priority 1: Match within user's branch
    if branch_id and lanes:
        for lane in lanes:
            if lane.get('branchID') == branch_id:
                l_from = (lane.get('fromUNLocode') or '').strip().upper()
                l_to = (lane.get('toUNLocode') or '').strip().upper()
                if l_from == origin and l_to == destination:
                    tt = (lane.get('trafficType') or '').strip().upper()
                    if tt in ('EX', 'IM'):
                        return jsonify({
                            'success': True,
                            'trafficType': tt,
                            'matched': True,
                            'matchedBy': 'transport_lane_branch',
                            'origin': origin,
                            'destination': destination,
                            'lane': {
                                'id': lane.get('id'),
                                'name': lane.get('name'),
                                'branchID': lane.get('branchID')
                            }
                        })
                        
    # Priority 2: Match across all branches
    if lanes:
        for lane in lanes:
            l_from = (lane.get('fromUNLocode') or '').strip().upper()
            l_to = (lane.get('toUNLocode') or '').strip().upper()
            if l_from == origin and l_to == destination:
                tt = (lane.get('trafficType') or '').strip().upper()
                if tt in ('EX', 'IM'):
                    return jsonify({
                        'success': True,
                        'trafficType': tt,
                        'matched': True,
                        'matchedBy': 'transport_lane_global',
                        'origin': origin,
                        'destination': destination,
                        'lane': {
                            'id': lane.get('id'),
                            'name': lane.get('name'),
                            'branchID': lane.get('branchID')
                        }
                    })

    # If not found in transport lanes API, return matched=False and no trafficType (no fallback)
    return jsonify({
        'success': True,
        'trafficType': None,
        'matched': False,
        'origin': origin,
        'destination': destination
    })


@customer.route('/api/get-schedules')
@login_required
def api_get_schedules():
    import requests
    pol = request.args.get('portOfLoading')
    pod = request.args.get('portOfDischarge')
    product = request.args.get('product', 'lcl')
    closing_date = request.args.get('closingDate')
    branch_id = request.args.get('branchID')
    
    if not branch_id and current_user.branches:
        try: branch_id = int(current_user.branches[0].branch_id)
        except: pass
    if not branch_id:
        branch_id = 23
        
    url = f"http://realnexus.comit.cloud:5000/api/Schedules"
    params = {
        'portOfLoading': pol,
        'portOfDischarge': pod,
        'product': product,
        'branchID': branch_id
    }
    if closing_date:
        params['closingDate'] = closing_date
        
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200 and isinstance(resp.json(), list) and len(resp.json()) > 0:
            return jsonify(resp.json())
        
        # Fallback 1: Broad date query if exact closing_date yielded 0 results
        if closing_date:
            params_broad = {
                'portOfLoading': pol,
                'portOfDischarge': pod,
                'product': product,
                'closingDate': '2026-01-01',
                'branchID': branch_id
            }
            resp_broad = requests.get(url, params=params_broad, headers=headers, timeout=5)
            if resp_broad.status_code == 200 and isinstance(resp_broad.json(), list) and len(resp_broad.json()) > 0:
                return jsonify(resp_broad.json())

        # Fallback 2: General query without date or branch filter
        params_fb = {
            'portOfLoading': pol,
            'portOfDischarge': pod,
            'product': product
        }
        resp_fb = requests.get(url, params=params_fb, headers=headers, timeout=5)
        if resp_fb.status_code == 200 and isinstance(resp_fb.json(), list):
            return jsonify(resp_fb.json())

        return jsonify([])
    except Exception as e:
        print(f"Error fetching schedules: {e}")
    return jsonify([])


@customer.route('/new-booking', methods=['GET', 'POST'])
@login_required
def new_booking():
    if current_user.role != 'customer':
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
        quote_data = get_booking_safely(quote_id, user_id=current_user.id)
        if not quote_data:
            quote_data = get_booking_safely(quote_id)
            
    
    # Fetch Countries
    from app.services.master_data import get_code_list
    try:
        countries_api = get_code_list('countrycode')
        countries = [c.to_dict() for c in countries_api] if countries_api else []
    except Exception as ex:
        print("Error fetching countries:", ex)
        countries = []

    # Fetch valid quotes for the quote picker
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    my_quotes = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status == 'Saved Quote'
    ).order_by(Booking.created_at.desc()).limit(100).all()

    valid_quotes = []
    for q in my_quotes:
        valid_until = q.created_at + timedelta(days=30)
        if valid_until >= now:
            computed_status = 'Expiring Soon' if (valid_until - now).days <= 2 else 'Active'
            q.computed_status = computed_status
            valid_quotes.append(q)

    return render_template('customer/new_booking.html', 
                         origins=origins, 
                         destinations=destinations,
                         query=session.get('search_query', {}),
                         quote_data=quote_data,
                         countries=countries,
                         valid_quotes=valid_quotes)

@customer.route('/rate-results')
@login_required
def rate_results():
    query = session.get('search_query')
    if not query:
        return redirect(url_for('customer.new_booking'))
        
    quote_number = query.get('quote_id') or query.get('api_quotation_id')
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
    
    if quote_number or cached_data:
        import requests
        data = None
        
        if quote_number:
            headers = {'accept': 'application/json', 'x-api-key': '1'}
            try:
                resp = requests.get(f"http://realnexus.comit.cloud:5000/api/Quotations/{quote_number}", headers=headers, timeout=10)
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
                
                api_id = header.get('quotationId') or header.get('fmsQuotationId') or quote_number or ''
                
                sailing = sailings[0] if sailings else {}
                pol = sailing.get('pol', {})
                pod = sailing.get('pod', {})
                
                # Calculate transit days from quote sailings
                import datetime
                transit_days = 0
                for s in sailings:
                    s_pol = s.get('pol', {}) if isinstance(s.get('pol'), dict) else {}
                    s_pod = s.get('pod', {}) if isinstance(s.get('pod'), dict) else {}
                    s_etd = s_pol.get('etd') or s.get('etd') or s.get('estimatedTimeOfDeparture')
                    s_eta = s_pod.get('eta') or s.get('eta') or s.get('estimatedTimeOfArrival')
                    if s_etd and s_eta:
                        try:
                            etd = datetime.datetime.strptime(str(s_etd)[:10], '%Y-%m-%d')
                            eta = datetime.datetime.strptime(str(s_eta)[:10], '%Y-%m-%d')
                            diff = (eta - etd).days
                            if diff > 0:
                                transit_days = diff
                                break
                        except Exception:
                            pass
                
                # Calculate total price & quotation currency safely
                lines = tariff.get('lines', []) or []
                total_cost = 0.0
                for l_item in lines:
                    try:
                        amt = float(l_item.get('amount') or 0.0)
                        total_cost += amt
                    except (ValueError, TypeError):
                        pass

                if not total_cost or total_cost <= 0:
                    for src in [header, tariff, data]:
                        if isinstance(src, dict):
                            for key in ['totalCost', 'totalAmount', 'amount', 'grandTotal']:
                                val = src.get(key)
                                if val is not None:
                                    try:
                                        t_val = float(val)
                                        if t_val > 0:
                                            total_cost = t_val
                                            break
                                    except (ValueError, TypeError):
                                        pass
                            if total_cost > 0:
                                break

                quotation_currency = (
                    tariff.get('quotationCurrency')
                    or header.get('currency')
                    or data.get('currency')
                    or (data.get('quotation', {}).get('header', {}).get('currency') if isinstance(data.get('quotation'), dict) else None)
                    or 'USD'
                )
                
                is_lcl = query.get('service_type', '') in ['Less than a container load', 'LCL']
                branch_name = 'Fast Transitline Antwerp'
                carrier_name = branch_name if is_lcl else (sailing.get('linerName') or 'Standard Carrier')
                nvocc_name = carrier_name
                
                # Fetch Schedules for Next Closing & Modal & Transit Days
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
                        branch_id = 23
                        if current_user.branches:
                            try: branch_id = int(current_user.branches[0].branch_id)
                            except: pass
                        c_date = None
                        if query.get('cargo_ready_date'):
                            c_date = str(query.get('cargo_ready_date'))[:10]
                        elif header.get('validFrom'):
                            c_date = str(header.get('validFrom'))[:10]

                        sched_url = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol_locode}&portOfDischarge={pod_locode}&product=lcl&branchID={branch_id}"
                        if c_date:
                            sched_url += f"&closingDate={c_date}"
                        sched_resp = requests.get(sched_url, headers={'accept': 'application/json', 'x-api-key': '1'}, timeout=5)
                        if sched_resp.status_code == 200:
                            schedules = sched_resp.json()
                            if not isinstance(schedules, list):
                                schedules = []
                        if not schedules and c_date:
                            sched_url_broad = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol_locode}&portOfDischarge={pod_locode}&product=lcl&closingDate=2026-01-01&branchID={branch_id}"
                            sched_resp_broad = requests.get(sched_url_broad, headers={'accept': 'application/json', 'x-api-key': '1'}, timeout=5)
                            if sched_resp_broad.status_code == 200:
                                schedules = sched_resp_broad.json()
                                if not isinstance(schedules, list):
                                    schedules = []
                        if not schedules:
                            sched_url_fb = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol_locode}&portOfDischarge={pod_locode}&product=lcl"
                            sched_resp_fb = requests.get(sched_url_fb, headers={'accept': 'application/json', 'x-api-key': '1'}, timeout=5)
                            if sched_resp_fb.status_code == 200:
                                schedules = sched_resp_fb.json()
                                if not isinstance(schedules, list):
                                    schedules = []
                    except Exception as e:
                        print(f"Failed to fetch schedules: {e}")

                # Calculate transit days from sailing schedules API if not already found
                if schedules:
                    for s in schedules:
                        s_etd = s.get('etd') or s.get('estimatedTimeOfDeparture')
                        s_eta = s.get('eta') or s.get('estimatedTimeOfArrival')
                        if s_etd and s_eta:
                            try:
                                etd_dt = datetime.datetime.strptime(str(s_etd)[:10], '%Y-%m-%d')
                                eta_dt = datetime.datetime.strptime(str(s_eta)[:10], '%Y-%m-%d')
                                diff = (eta_dt - etd_dt).days
                                if diff > 0:
                                    transit_days = diff
                                    break
                            except Exception:
                                pass

                # Fallback to local DB rate transit days if still 0
                if transit_days <= 0:
                    try:
                        db_rate = Rate.query.filter(
                            Rate.origin.ilike(f"%{pol_locode}%"),
                            Rate.destination.ilike(f"%{pod_locode}%")
                        ).first()
                        if not db_rate:
                            o_clean = query.get('origin', '').split('(')[0].strip()
                            d_clean = query.get('destination', '').split('(')[0].strip()
                            if o_clean and d_clean:
                                db_rate = Rate.query.filter(
                                    Rate.origin.ilike(f"%{o_clean}%"),
                                    Rate.destination.ilike(f"%{d_clean}%")
                                ).first()
                        if db_rate and db_rate.transit_days and db_rate.transit_days > 0:
                            transit_days = db_rate.transit_days
                    except Exception:
                        pass

                # Only keep transit days if found from real schedules or DB rate
                if transit_days <= 0:
                    transit_days = None

                # Calculate next closing date dynamically only from real schedules
                if schedules:
                    for s in schedules:
                        c_val = s.get('closingLCL') or s.get('closing') or s.get('etd') or s.get('estimatedTimeOfDeparture')
                        if c_val:
                            try:
                                next_closing = datetime.datetime.strptime(str(c_val)[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                                break
                            except Exception:
                                next_closing = str(c_val)[:10]
                                break

                # Fallback to Quotation POL if Schedules API is empty
                if not next_closing and pol:
                    closing_val = pol.get('closingLcl') if is_lcl else pol.get('closing')
                    if not closing_val:
                        closing_val = pol.get('closing') or pol.get('etd')
                    if closing_val:
                        try:
                            next_closing = datetime.datetime.strptime(str(closing_val)[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                        except:
                            next_closing = str(closing_val)[:10]

                validity_end = header.get('validUntil', 'N/A')
                is_lcl = query.get('service_type', '') in ['Less than a container load', 'LCL']
                
                # Dynamically resolve branch/carrier name from API response or branch lookup
                branch_name = header.get('branchName') or header.get('nvoccName') or header.get('carrierName')
                if not branch_name and current_user.branches:
                    for b in current_user.branches:
                        if str(getattr(b, 'branch_id', '')) == str(header.get('branchId')):
                            branch_name = getattr(b, 'branch_name', None) or f"Branch #{b.branch_id}"
                            break
                if not branch_name:
                    branch_name = f"Branch #{header.get('branchId')}" if header.get('branchId') else '—'
                
                carrier_name = 'LCL Direct Consolidation' if is_lcl else 'FCL Ocean Service'
                if schedules and len(schedules) > 0 and schedules[0].get('vessel'):
                    carrier_name = f"{schedules[0].get('vessel')} ({schedules[0].get('voyage') or 'Direct'})"
                nvocc_name = branch_name
                
                # Check dynamic charge cost groups from API tariff lines
                t_type = (query.get('traffic_type') or header.get('trafficType') or 'EX').upper()
                if t_type == 'IM':
                    # For Import, European local charges (LC) are Destination Charges
                    has_origin_charges = any((l.get('articleCostGroup') or '').upper() in ['OLC'] for l in lines)
                    has_destination_charges = any(
                        (l.get('articleCostGroup') or '').upper() in ['LC', 'DC', 'DLC', 'DL']
                        or l.get('isLocalCharge') is True
                        for l in lines
                    )
                else:
                    # For Export, European local charges (LC) are Origin Charges
                    has_origin_charges = any(
                        (l.get('articleCostGroup') or '').upper() in ['LC', 'OLC']
                        or l.get('isLocalCharge') is True
                        for l in lines
                    )
                    has_destination_charges = any((l.get('articleCostGroup') or '').upper() in ['DC', 'DLC', 'DL'] for l in lines)

                has_freight_charges = any(
                    (l.get('articleCostGroup') or '').upper() in ['FC', 'AC']
                    or any(term in (l.get('articleName') or '').upper() for term in ['FREIGHT', 'OCEAN', 'SURCHARGE', 'BAF', 'CAF', 'ETS', 'FUEL'])
                    for l in lines
                )
                
                # Resolve cargo details for Rate Results display
                cargo_items = query.get('cargo_items', []) or []
                commodities = data.get('commodities', []) or (data.get('quotation', {}).get('commodities', []) if isinstance(data.get('quotation'), dict) else [])

                rr_vol = float(query.get('volume') or 0.0)
                if not rr_vol and commodities:
                    rr_vol = sum(float(c.get('volume') or 0.0) for c in commodities)

                rr_weight = 0.0
                if commodities:
                    rr_weight = sum(float(c.get('weight') or 0.0) for c in commodities)
                elif cargo_items:
                    rr_weight = sum(float(c.get('weight') or 0.0) for c in cargo_items if isinstance(c, dict))

                rr_packages = ""
                if commodities:
                    rr_packages = ", ".join([f"{c.get('nrPackages', 1)} x {c.get('packageCode') or c.get('packageTypeDescription') or 'Pkg'}" for c in commodities])
                elif cargo_items:
                    rr_packages = ", ".join([f"{c.get('qty', 1)} x {c.get('type') or 'Pkg'}" for c in cargo_items if isinstance(c, dict) and c.get('qty')])

                rr_commodity = ""
                if commodities:
                    rr_commodity = commodities[0].get('commodityDescription', '')
                elif cargo_items and isinstance(cargo_items[0], dict):
                    rr_commodity = cargo_items[0].get('desc') or cargo_items[0].get('commodityDescription', '')

                cargo_details = {
                    'volume': rr_vol,
                    'weight': rr_weight,
                    'packages': rr_packages,
                    'commodity': rr_commodity
                }

                # Format to match the frontend expectations while passing real API data
                results = [{
                    'api_quote': data,
                    'total_cost': total_cost,
                    'quotation_currency': quotation_currency,
                    'cargo_details': cargo_details,
                    'transit_days': transit_days,
                    'carrier': carrier_name,
                    'frequency': 'Weekly',
                    'ui_tag': 'Official API Quote',
                    'next_closing': next_closing,
                    'schedules': schedules,
                    'has_origin_charges': has_origin_charges,
                    'has_freight_charges': has_freight_charges,
                    'has_destination_charges': has_destination_charges,
                    'rate': {
                        'nvocc_name': nvocc_name,
                        'validity_end': validity_end,
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
        flash('Administrators cannot place bookings directly.', 'warning')
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
    
    db.session.commit()
    
    # Fire off API request in background thread
    try:
        from app.utils import bg_executor, run_in_app_context
        bg_executor.submit(run_in_app_context, current_app._get_current_object(), post_booking_to_api, booking.id)
    except Exception as e:
        current_app.logger.error(f"Failed to submit background API post: {e}")
    
    if request.is_json:
        return jsonify({'success': True, 'booking_id': booking.id, 'message': 'Booking confirmed!'})
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
    
    db.session.commit()
    
    # Fire off API request in background thread
    try:
        from app.utils import bg_executor, run_in_app_context
        bg_executor.submit(run_in_app_context, current_app._get_current_object(), post_booking_to_api, booking.id)
    except Exception as e:
        current_app.logger.error(f"Failed to submit background API post: {e}")
    
    if request.is_json:
        return jsonify({'success': True, 'booking_id': booking.id, 'message': 'Booking request submitted!'})
    flash('Booking request submitted! We will review it shortly.', 'success')
    return redirect(url_for('customer.my_shipments'))

import math
import urllib.parse

class ApiBookingItem:
    """Wrapper around ERP /api/Bookings JSON response for template rendering."""
    def __init__(self, raw):
        self.raw = raw or {}
        self.id = self.raw.get('bookingId') or self.raw.get('bookingID') or self.raw.get('id') or 0
        self.booking_id = self.id
        self.bookingId = self.id
        self.bookingref = self.raw.get('bookingRef') or self.raw.get('bookingref') or self.raw.get('bookingNumber') or ''
        self.bookingRef = self.bookingref
        self.api_booking_ref = self.bookingref
        self.customerReference = self.raw.get('customerReference') or self.raw.get('customerRef') or ''
        self.customerRef = self.customerReference
        self.customer_ref = self.customerReference
        self.file_ref = self.raw.get('fileRef') or ''
        self.fileRef = self.file_ref
        
        # Parse Dates (strictly no fallback to datetime.utcnow())
        self.created_at = self._parse_date(self.raw.get('createdOn'))
        self.createdOn = self.raw.get('createdOn') or ''
        self.etd = self._parse_date(self.raw.get('etd'))
        self.atd = self._parse_date(self.raw.get('atd'))
        self.eta_pod = self._parse_date(self.raw.get('eta'))
        self.eta = self.eta_pod
        self.ata = self._parse_date(self.raw.get('ata'))

        raw_status = (self.raw.get('status') or '').strip()
        if self.ata or any(w in raw_status.lower() for w in ['deliver', 'arrived', 'complete']):
            self.status = 'Delivered'
        elif self.atd or any(w in raw_status.lower() for w in ['transit', 'depart', 'dispatched', 'sailing']):
            self.status = 'In Transit'
        elif raw_status:
            self.status = raw_status.capitalize()
        else:
            self.status = None
        
        self.product = (self.raw.get('product') or '').strip()
        self.service_type = self.product
        self.selected_nvocc = self.raw.get('vessel') or ''
        self.vessel = self.raw.get('vessel') or ''
        self.vessel_name = self.vessel
        self.voyage = self.raw.get('voyage') or ''
        self.voyage_number = self.voyage
        
        # Origin: ISNULL(porlocation, pollocation)
        self.porLocation = self.raw.get('porLocation') or ''
        self.porlocation = self.porLocation
        self.place_of_receipt = self.porLocation
        self.polLocation = self.raw.get('polLocation') or ''
        self.pollocation = self.polLocation
        self.origin = (self.porLocation.strip() or self.polLocation.strip()) or ''
        
        # Destination: ISNULL(dellocation, podlocation)
        self.delLocation = self.raw.get('delLocation') or ''
        self.dellocation = self.delLocation
        self.place_of_delivery = self.delLocation
        self.podLocation = self.raw.get('podLocation') or ''
        self.podlocation = self.podLocation
        self.destination = (self.delLocation.strip() or self.podLocation.strip()) or ''

        # Locodes
        self.polLocode = self.raw.get('polLocode') or ''
        self.podLocode = self.raw.get('podLocode') or ''
        self.porLocode = self.raw.get('porLocode') or ''
        self.delLocode = self.raw.get('delLocode') or ''
        
        # Quantities (None if not provided in API, strictly no fallback)
        self.totalcolli = self.raw.get('totalColli')
        self.totalColli = self.totalcolli
        self.totalweight = self.raw.get('totalWeight')
        self.totalWeight = self.totalweight
        self.totalVolume = self.raw.get('totalVolume')
        self.totalvolume = self.totalVolume
        self.volume = self.totalVolume
        
        # Quote number
        self.quotenumber = self.raw.get('quoteNumber') or self.raw.get('quotationRef') or ''
        self.quoteNumber = self.quotenumber
        self.quote_number = self.quotenumber
        
        # ERP detail fields
        self.ops_manager = self.raw.get('opsManager') or ''
        self.customer_name = self.raw.get('customerName') or ''
        self.customer_contact = self.raw.get('customerContactName') or ''
        self.shipper_name = self.raw.get('shipperName') or ''
        self.shipper_contact = self.raw.get('shipperContactName') or ''
        self.consignee_name = self.raw.get('consigneeName') or ''
        self.consignee_contact = self.raw.get('consigneeContactName') or ''
        self.notify_party = self.raw.get('notifyParty') or ''
        self.notify_contact = self.raw.get('notifyContact') or ''
        self.special_instructions = self.raw.get('specialInstructions') or ''
        self.internal_memo = self.raw.get('internalMemo') or ''
        self.destination_contact = self.raw.get('cfsDestinationRef') or ''
        self.inco_term = self.raw.get('incoTerm') or ''
        self.inco_location = self.raw.get('incoLocation') or ''
        self.payment_method = self.raw.get('paymentMethod') or ''
        self.traffic_type = self.raw.get('trafficType') or ''
        self.created_by = self.raw.get('createdBy') or ''
        self.tp_lane_id = self.raw.get('tpLaneId')
        self.uuid = self.bookingref
        self.via_port = ''
        
        PKG_MAP = {
            'BX': 'Box', 'PX': 'Pallet', 'CR': 'Crate', 'DR': 'Drum', 'BG': 'Bag',
            'ZR': 'IBC', 'CT': 'Carton', 'CTN': 'Carton', 'CS': 'Case', 'CL': 'Colis',
            'SK': 'Skid', 'RL': 'Roll', '20CN': "20' Container", '40CN': "40' Container",
            'PALLET': 'Pallet', 'PALLETS': 'Pallet', 'PACKAGES': 'Package', 'PACKAGE': 'Package',
            'BUNDLES': 'Bundle', 'BUNDLE': 'Bundle', 'BAGS': 'Bag', 'BAG': 'Bag'
        }
        
        # Commodities & Cargo items directly from API
        self.cargo_items = []
        pkg_parts = []
        c_weight = float(self.totalweight) if self.totalweight is not None else 0.0
        c_vol = float(self.totalVolume) if self.totalVolume is not None else 0.0
        
        raw_commodities = self.raw.get('commodities') or []
        for com in raw_commodities:
            p_desc = com.get('packageTypeDescription') or ''
            p_code = com.get('packageCode') or ''
            p_label = p_desc or PKG_MAP.get(str(p_code).upper().strip(), str(p_code))
            n_pkg = com.get('nrPackages')
            if n_pkg is not None and p_label:
                pkg_parts.append(f"{n_pkg} x {p_label}")
            elif n_pkg is not None:
                pkg_parts.append(f"{n_pkg} pcs")
            elif p_label:
                pkg_parts.append(p_label)
                
            w_val = com.get('weight') if com.get('weight') is not None else com.get('grossWeight')
            v_val = com.get('volume')
            if not c_weight and w_val is not None:
                try: c_weight += float(w_val)
                except Exception: pass
            if not c_vol and v_val is not None:
                try: c_vol += float(v_val)
                except Exception: pass
                
            item_mock = type('CargoItemMock', (), {
                'quantity': n_pkg,
                'package_type': p_label,
                'weight_kg': float(w_val) if w_val is not None else None,
                'volume_cbm': float(v_val) if v_val is not None else None,
                'description': com.get('commodityDescription') or com.get('goodsDescription') or '',
                'marks_numbers': com.get('marksNumbers') or '',
                'hs_code': com.get('hsCode') or '',
                'dimensions': com.get('dimensions') or [],
                'is_imo': bool(com.get('isHazmat', False))
            })()
            self.cargo_items.append(item_mock)
            
        if not pkg_parts and self.totalcolli:
            pkg_parts.append(f"{self.totalcolli} pcs")
            
        if pkg_parts or c_weight > 0 or c_vol > 0:
            summary_bits = []
            if pkg_parts:
                summary_bits.append(", ".join(pkg_parts))
            if c_weight > 0:
                summary_bits.append(f"{c_weight:.2f} kg")
            if c_vol > 0:
                summary_bits.append(f"{c_vol:.2f} m³")
            self.cargo_summary = " · ".join(summary_bits)
        else:
            self.cargo_summary = None
            
        self.attachments = []
        self.tracking_events = []
        self.shipping_instruction = None
        self.total_cost = 0.0
        self.freight_terms = self.raw.get('freightTerms') or ''
        self.general_description = self.raw.get('specialInstructions') or ''
        self.general_terms = ''
        self.pickup_address = ''
        self.user_id = 0
        self.is_si_submitted = False

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.id,
            'booking_ref': self.bookingref,
            'customer_ref': self.customer_ref,
            'file_ref': self.file_ref,
            'status': self.status,
            'origin': self.origin,
            'destination': self.destination,
            'service_type': self.service_type,
            'selected_nvocc': self.selected_nvocc,
            'vessel_name': self.vessel_name,
            'voyage_number': self.voyage_number,
            'total_pieces': self.totalcolli,
            'total_weight': self.totalweight,
            'total_volume': self.totalVolume,
            'cargo_summary': self.cargo_summary,
            'created_at': self.created_at.strftime('%d %b %Y') if self.created_at else None,
            'created_at_iso': self.created_at.isoformat() if self.created_at else None,
            'etd': self.etd.strftime('%d %b %Y') if self.etd else None,
            'atd': self.atd.strftime('%d %b %Y') if self.atd else None,
            'eta': self.eta.strftime('%d %b %Y') if self.eta else None,
            'ata': self.ata.strftime('%d %b %Y') if self.ata else None,
            'ops_manager': self.ops_manager or None,
            'customer_name': self.customer_name or None,
            'customer_contact': self.customer_contact or None,
            'shipper_name': self.shipper_name or None,
            'consignee_name': self.consignee_name or None,
            'notify_party': self.notify_party or None,
            'special_instructions': self.special_instructions or None,
            'inco_term': self.inco_term or None,
            'inco_location': self.inco_location or None,
            'payment_method': self.payment_method or None,
            'commodities': [
                {
                    'quantity': getattr(item, 'quantity', None),
                    'package_type': getattr(item, 'package_type', None),
                    'weight_kg': getattr(item, 'weight_kg', None),
                    'volume_cbm': getattr(item, 'volume_cbm', None),
                    'description': getattr(item, 'description', None),
                    'marks_numbers': getattr(item, 'marks_numbers', None),
                    'dimensions': getattr(item, 'dimensions', []),
                    'hs_code': getattr(item, 'hs_code', None),
                    'is_imo': getattr(item, 'is_imo', False)
                } for item in self.cargo_items
            ]
        }
        
    def _parse_date(self, d_val):
        if not d_val:
            return None
        if isinstance(d_val, datetime):
            return d_val
        try:
            cleaned = str(d_val).replace('Z', '')
            if '.' in cleaned:
                cleaned = cleaned.split('.')[0]
            if 'T' in cleaned:
                return datetime.fromisoformat(cleaned)
            return datetime.strptime(cleaned[:10], '%Y-%m-%d')
        except Exception:
            return None

class ApiPagination:
    """Emulates Flask-SQLAlchemy Pagination object for render_pagination macro."""
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = int(page or 1)
        self.per_page = int(per_page or 10)
        self.total = int(total or len(items))
        self.pages = max(1, math.ceil(self.total / self.per_page)) if self.per_page else 1
        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages
        self.prev_num = self.page - 1 if self.has_prev else None
        self.next_num = self.page + 1 if self.has_next else None

    def to_dict(self):
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total_records': self.total,
            'total_pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_num': self.prev_num,
            'next_num': self.next_num
        }

    def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or 
                (num >= self.page - left_current and num <= self.page + right_current) or 
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num

_SHIPMENTS_CACHE = {} # (account_id, page, per_page): (expires_at, items, total_records)

@customer.route('/api/my-shipments', endpoint='api_my_shipments')
@customer.route('/my-shipments', endpoint='my_shipments')
@login_required
def my_shipments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    account_id = _resolve_customer_account_id(4128)
    cache_key = (account_id, page, per_page)
    now = time.time()
    
    # Check 45-second high-speed in-memory cache
    if cache_key in _SHIPMENTS_CACHE:
        expires_at, cached_items, cached_total = _SHIPMENTS_CACHE[cache_key]
        if now < expires_at:
            pagination = ApiPagination(cached_items, page, per_page, cached_total)
            if request.is_json or '/api/my-shipments' in request.path or request.args.get('format') == 'json':
                return jsonify({
                    'shipments': [it.to_dict() for it in cached_items],
                    'pagination': pagination.to_dict()
                })
            return render_template('customer/shipments.html', shipments=cached_items, pagination=pagination)

    url = "http://realnexus.comit.cloud:5000/api/Bookings"
    params = {
        "accountId": account_id,
        "page": page,
        "pageSize": per_page
    }
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    
    items = []
    total_records = 0
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            raw_bookings = data.get('bookings', [])
            total_records = data.get('pagination', {}).get('totalRecords', len(raw_bookings))
            
            # Pre-fetch commodities in parallel for complete cargo display
            import concurrent.futures
            global _GLOBAL_BOOKING_DETAILS_CACHE
            if '_GLOBAL_BOOKING_DETAILS_CACHE' not in globals():
                globals()['_GLOBAL_BOOKING_DETAILS_CACHE'] = {}
            bkg_cache = globals()['_GLOBAL_BOOKING_DETAILS_CACHE']

            def _fetch_bkg_commodities(b_raw):
                b_ref = b_raw.get('bookingRef')
                if not b_ref:
                    return None, []
                if b_ref in bkg_cache:
                    return b_ref, bkg_cache[b_ref]
                try:
                    q_ref = urllib.parse.quote(b_ref, safe='')
                    u = f"http://realnexus.comit.cloud:5000/api/Bookings/{q_ref}?accountId={account_id}"
                    r_d = requests.get(u, headers=headers, timeout=2.5)
                    if r_d.status_code == 200:
                        comms = r_d.json().get('commodities', [])
                        bkg_cache[b_ref] = comms
                        return b_ref, comms
                except Exception:
                    pass
                return b_ref, []

            try:
                items_needing_commodities = [b for b in raw_bookings if not b.get('commodities')]
                if items_needing_commodities:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(items_needing_commodities))) as executor:
                        results = list(executor.map(_fetch_bkg_commodities, items_needing_commodities))
                        for b_ref, comms in results:
                            if b_ref and comms:
                                for b_raw in raw_bookings:
                                    if b_raw.get('bookingRef') == b_ref:
                                        b_raw['commodities'] = comms
            except Exception as ex:
                current_app.logger.error(f"Parallel booking commodities fetch error: {ex}")

            items = [ApiBookingItem(b) for b in raw_bookings]
            _SHIPMENTS_CACHE[cache_key] = (now + 45, items, total_records)
        else:
            current_app.logger.error(f"API bookings returned {resp.status_code}: {resp.text}")
    except Exception as e:
        current_app.logger.error(f"Error fetching API bookings: {e}")
        
    pagination = ApiPagination(items, page, per_page, total_records)
    if request.is_json or '/api/my-shipments' in request.path or request.args.get('format') == 'json':
        return jsonify({
            'shipments': [it.to_dict() for it in items],
            'pagination': pagination.to_dict()
        })
    return render_template('customer/shipments.html', shipments=items, pagination=pagination)

@customer.route('/shipments/export-excel')
@login_required
def export_shipments_excel():
    import pandas as pd
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    
    account_id = _resolve_customer_account_id(4128)
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    items = []
    
    try:
        url = "http://realnexus.comit.cloud:5000/api/Bookings"
        resp = requests.get(url, params={"accountId": account_id, "pageSize": 500}, headers=headers, timeout=8)
        if resp.status_code == 200:
            raw_bookings = resp.json().get('bookings', [])
            items = [ApiBookingItem(b) for b in raw_bookings]
    except Exception as e:
        current_app.logger.error(f"Error fetching API bookings for export: {e}")
        
    rows = []
    for it in items:
        rows.append({
            'Booking Reference': it.bookingref or f'BK-{it.id}',
            'Customer Ref': it.customer_ref or '',
            'Status': it.status or '',
            'Origin Port': it.origin or '',
            'Destination Port': it.destination or '',
            'Service Type': it.service_type or '',
            'Vessel': it.vessel_name or '',
            'Voyage': it.voyage_number or '',
            'Total Pieces': it.totalcolli if it.totalcolli else '',
            'Gross Weight (kg)': f"{it.totalweight:.2f}" if it.totalweight else '',
            'Volume (m³)': f"{it.totalVolume:.2f}" if it.totalVolume else '',
            'Cargo Details': it.cargo_summary or '',
            'ETD (Departure)': it.etd.strftime('%Y-%m-%d') if it.etd else '',
            'ATD (Departed)': it.atd.strftime('%Y-%m-%d') if it.atd else '',
            'ETA (Arrival)': it.eta.strftime('%Y-%m-%d') if it.eta else '',
            'ATA (Delivered)': it.ata.strftime('%Y-%m-%d') if it.ata else '',
            'Created Date': it.created_at.strftime('%Y-%m-%d') if it.created_at else ''
        })
        
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=[
            'Booking Reference', 'Customer Ref', 'Status', 'Origin Port', 'Destination Port',
            'Service Type', 'Vessel', 'Voyage', 'Total Pieces', 'Gross Weight (kg)',
            'Volume (m³)', 'Cargo Details', 'ETD (Departure)', 'ATD (Departed)',
            'ETA (Arrival)', 'ATA (Delivered)', 'Created Date'
        ])
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Shipments', index=False)
        sheet = writer.sheets['Shipments']
        
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )
        
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet.row_dimensions[1].height = 28
        
        for r_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
            sheet.row_dimensions[r_idx].height = 20
            is_alt = (r_idx % 2 == 0)
            for cell in row:
                cell.font = regular_font
                cell.border = thin_border
                if is_alt:
                    cell.fill = alt_fill
                cell.alignment = Alignment(vertical="center")
                
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            sheet.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 45)
            
    output.seek(0)
    filename = f"FTL_Shipments_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)

@customer.route('/quotes/export-excel')
@login_required
def export_quotes_excel():
    import pandas as pd
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    
    customer_id = 1
    if current_user.accounts:
        try: customer_id = int(current_user.accounts[0].account_id)
        except: pass
        
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    quotes_list = []
    try:
        url = "http://realnexus.comit.cloud:5000/api/Quotations"
        resp = requests.get(url, params={"accountId": customer_id, "pageSize": 500}, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                quotes_list = data
            elif isinstance(data, dict):
                quotes_list = data.get('items', data.get('quotations', data.get('quotes', [])))
    except Exception as e:
        current_app.logger.error(f"Error fetching API quotes for export: {e}")
        
    rows = []
    now = datetime.utcnow()
    for it in quotes_list:
        q_item = it.get('quotation', it)
        header = q_item.get('header', q_item)
        tariff = q_item.get('tariff', {}) or {}
        
        quote_id = header.get('quotationId')
        prefix1 = header.get('quoPrefix1', 'QUO')
        prefix2 = header.get('quoPrefix2', '2026')
        quote_num = header.get('quoteNumber') or header.get('quotationNo') or f"{prefix1}-{prefix2}-{quote_id}"
        
        routing = header.get('routing', header.get('route', {})) or {}
        por = routing.get('porLocation') or header.get('porLocation') or ''
        pol = routing.get('polLocation') or header.get('polLocation') or ''
        del_loc = routing.get('delLocation') or header.get('delLocation') or ''
        pod = routing.get('podLocation') or header.get('podLocation') or ''
        origin = por or pol or 'Unknown'
        destination = del_loc or pod or 'Unknown'
        
        created_on = str(header.get('createdOn') or '')[:10]
        valid_until_raw = str(header.get('validUntil') or header.get('validuntil') or '')[:10]
        valid_from_raw = str(header.get('validFrom') or header.get('validfrom') or '')[:10]
        
        valid_until_dt = now
        try:
            if valid_until_raw:
                valid_until_dt = datetime.strptime(valid_until_raw, '%Y-%m-%d')
        except: pass
        
        if valid_until_dt < now:
            c_status = 'Expired'
        elif (valid_until_dt - now).days <= 2:
            c_status = 'Expiring Soon'
        else:
            c_status = 'Active'
            
        total_cost = 0.0
        currency = header.get('currency') or tariff.get('quotationCurrency') or 'EUR'
        for line in tariff.get('lines', []):
            try:
                amt = float(line.get('sellAmount') or line.get('totalAmount') or line.get('amount') or 0.0)
                if amt > 0: total_cost += amt
            except: pass
            
        rows.append({
            'Quote Number': quote_num,
            'Customer Reference': header.get('customerReference') or '',
            'Status': c_status,
            'Origin Port': origin,
            'Destination Port': destination,
            'Service Type': header.get('freightTransportType') or 'LCL',
            'Carrier / NVOCC': header.get('nvoccName') or header.get('carrierName') or '',
            'Total Pieces': header.get('totalColli') or '',
            'Total Weight (kg)': header.get('totalWeight') or '',
            'Total Volume (m³)': header.get('totalVolume') or '',
            'Total Amount': f"{total_cost:.2f}" if total_cost > 0 else '',
            'Currency': currency,
            'Valid From': valid_from_raw,
            'Valid Until': valid_until_raw,
            'Created Date': created_on
        })
        
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=[
            'Quote Number', 'Customer Reference', 'Status', 'Origin Port', 'Destination Port',
            'Service Type', 'Carrier / NVOCC', 'Total Pieces', 'Total Weight (kg)',
            'Total Volume (m³)', 'Total Amount', 'Currency', 'Valid From', 'Valid Until', 'Created Date'
        ])
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Quotations', index=False)
        sheet = writer.sheets['Quotations']
        
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )
        
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet.row_dimensions[1].height = 28
        
        for r_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
            sheet.row_dimensions[r_idx].height = 20
            is_alt = (r_idx % 2 == 0)
            for cell in row:
                cell.font = regular_font
                cell.border = thin_border
                if is_alt:
                    cell.fill = alt_fill
                cell.alignment = Alignment(vertical="center")
                
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            sheet.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 40)
            
    output.seek(0)
    filename = f"FTL_Quotes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)

@customer.route('/api/shipment/<path:booking_id>', endpoint='api_shipment_detail_path')
@customer.route('/api/shipment/<booking_id>', endpoint='api_shipment_detail')
@customer.route('/shipment/<path:booking_id>', endpoint='shipment_detail_path')
@customer.route('/shipment/<int:booking_id>', endpoint='shipment_detail_int')
@customer.route('/shipment/<booking_id>', endpoint='shipment_detail')
@login_required
def shipment_detail(booking_id):
    headers = {'accept': 'application/json', 'x-api-key': '1'}
    ref_cand = urllib.parse.unquote(str(booking_id)).strip()
    candidate_accounts = _get_candidate_account_ids(4128)
    
    booking_obj = None
    list_item = None
    detail_data = None
    resolved_account_id = None
    
    # 1. If ref_cand contains '/' (PREFIX1/PREFIX2/COUNTER format), query detail API directly
    if '/' in ref_cand:
        for acc in candidate_accounts:
            try:
                url = f"http://realnexus.comit.cloud:5000/api/Bookings/{urllib.parse.quote(ref_cand, safe='')}"
                r_d = requests.get(url, params={'accountId': acc}, headers=headers, timeout=5)
                if r_d.status_code == 200:
                    detail_data = r_d.json()
                    resolved_account_id = acc
                    break
            except Exception as e:
                current_app.logger.error(f"Error fetching detail API for acc {acc}: {e}")
                
    # 2. Fetch bookings from list to get accurate tracking dates & status (ata, atd, eta, etd, status, fileRef, product)
    search_accounts = [resolved_account_id] if resolved_account_id else candidate_accounts
    for acc in search_accounts:
        try:
            r_list = requests.get("http://realnexus.comit.cloud:5000/api/Bookings", params={'accountId': acc, 'pageSize': 100}, headers=headers, timeout=5)
            if r_list.status_code == 200:
                for b_raw in r_list.json().get('bookings', []):
                    b_id_str = str(b_raw.get('bookingId') or '')
                    b_ref_str = str(b_raw.get('bookingRef') or '')
                    if ref_cand in [b_id_str, b_ref_str] or ref_cand.replace('/', '') == b_ref_str.replace('/', ''):
                        list_item = b_raw
                        resolved_account_id = acc
                        break
            if list_item:
                break
        except Exception as e:
            current_app.logger.error(f"Error fetching booking list from API for acc {acc}: {e}")

    # 3. If detail_data not yet retrieved (e.g. numeric ID), fetch using resolved b_ref
    if not detail_data:
        b_ref = (list_item.get('bookingRef') if list_item else ref_cand) or ''
        acc_to_use = resolved_account_id or (candidate_accounts[0] if candidate_accounts else 4128)
        if b_ref and '/' in b_ref:
            try:
                url = f"http://realnexus.comit.cloud:5000/api/Bookings/{urllib.parse.quote(str(b_ref).strip(), safe='')}"
                r_d = requests.get(url, params={'accountId': acc_to_use}, headers=headers, timeout=5)
                if r_d.status_code == 200:
                    detail_data = r_d.json()
            except Exception as e:
                current_app.logger.error(f"Error fetching booking detail API: {e}")

    # 4. Merge data from list and detail without adding any artificial fallbacks
    if list_item or detail_data:
        merged = {}
        if list_item:
            merged.update(list_item)
        if detail_data:
            for k, v in detail_data.items():
                if v is not None or k not in merged:
                    merged[k] = v
            # Ensure tracking dates and status from list are preserved
            for k in ['ata', 'atd', 'eta', 'etd', 'status', 'product', 'fileRef']:
                if list_item and list_item.get(k) is not None:
                    merged[k] = list_item.get(k)
        booking_obj = ApiBookingItem(merged)

    if not booking_obj:
        if request.is_json or '/api/shipment/' in request.path:
            return jsonify({'success': False, 'message': 'Shipment not found'}), 404
        abort(404)
        
    if request.is_json or '/api/shipment/' in request.path or request.args.get('format') == 'json':
        return jsonify({'success': True, 'booking': booking_obj.to_dict()})

    return render_template('customer/shipment_detail.html', booking=booking_obj)

@customer.route('/edit-booking/<booking_id>', methods=['GET', 'POST'])
@customer.route('/edit-booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = get_booking_safely(booking_id, user_id=current_user.id)
    if not booking:
        booking = get_booking_safely(booking_id)
    if not booking:
        abort(404)
    
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
from flask import send_file, abort

@customer.route('/shipment/<booking_id>/download-doc/<doc_type>')
@customer.route('/shipment/<int:booking_id>/download-doc/<doc_type>')
@login_required
def download_document(booking_id, doc_type):
    booking = get_booking_safely(booking_id, user_id=current_user.id)
    if not booking:
        booking = get_booking_safely(booking_id)
    if not booking:
        abort(404)
    
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

@customer.route('/shipment/<booking_id>/download-all-docs')
@customer.route('/shipment/<int:booking_id>/download-all-docs')
@login_required
def download_all_docs(booking_id):
    booking = get_booking_safely(booking_id, user_id=current_user.id)
    if not booking:
        booking = get_booking_safely(booking_id)
    if not booking:
        abort(404)
    
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

@customer.route('/shipment/<booking_id>/submit-si', methods=['GET', 'POST'])
@customer.route('/shipment/<int:booking_id>/submit-si', methods=['GET', 'POST'])
@login_required
def submit_si(booking_id):
    booking = get_booking_safely(booking_id, user_id=current_user.id)
    if not booking:
        booking = get_booking_safely(booking_id)
    if not booking:
        abort(404)
    
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


@customer.route('/schedules')
@login_required
def schedules():
    return render_template('customer/schedules.html')


@customer.route('/api/schedules-search')
@login_required
def api_schedules_search():
    pol = request.args.get('pol', '').strip()
    pod = request.args.get('pod', '').strip()
    c_date = request.args.get('closingDate', '').strip()
    
    branch_id = 23
    if current_user.branches:
        try:
            branch_id = int(current_user.branches[0].branch_id)
        except Exception:
            pass

    headers = {'accept': 'application/json', 'x-api-key': '1'}
    
    if not pol or not pod:
        return jsonify({'schedules': [], 'message': 'POL and POD are required.'})

    sched_url = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol}&portOfDischarge={pod}&product=lcl&branchID={branch_id}"
    if c_date:
        sched_url += f"&closingDate={c_date}"
        
    schedules = []
    try:
        resp = requests.get(sched_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                schedules = data
        
        # Fallback to broader search if specific date yielded no results
        if not schedules and c_date:
            sched_url_broad = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol}&portOfDischarge={pod}&product=lcl&closingDate=2026-01-01&branchID={branch_id}"
            resp_broad = requests.get(sched_url_broad, headers=headers, timeout=5)
            if resp_broad.status_code == 200 and isinstance(resp_broad.json(), list):
                schedules = resp_broad.json()

        if not schedules:
            sched_url_fb = f"http://realnexus.comit.cloud:5000/api/Schedules?portOfLoading={pol}&portOfDischarge={pod}&product=lcl"
            resp_fb = requests.get(sched_url_fb, headers=headers, timeout=5)
            if resp_fb.status_code == 200 and isinstance(resp_fb.json(), list):
                schedules = resp_fb.json()
    except Exception as e:
        print(f"Error searching schedules: {e}")

    return jsonify({'schedules': schedules})


_PORTS_LIST_CACHE = {
    'expires_at': 0,
    'data': None
}

@customer.route('/api/ports-list')
@login_required
def api_ports_list():
    now = time.time()
    if _PORTS_LIST_CACHE['data'] is not None and now < _PORTS_LIST_CACHE['expires_at']:
        return jsonify(_PORTS_LIST_CACHE['data'])

    headers = {'accept': 'application/json', 'x-api-key': '1'}
    all_ports_dict = {}

    try:
        op_resp = requests.get('http://realnexus.comit.cloud:5000/api/Ports/OriginPorts', headers=headers, timeout=5)
        if op_resp.status_code == 200:
            for p in op_resp.json():
                code = (p.get('code') or p.get('unlocode') or p.get('locode') or '').strip()
                name = (p.get('name') or p.get('portName') or code).strip()
                country = (p.get('country') or p.get('countryName') or '').strip()
                if code and name:
                    all_ports_dict[code] = {'code': code, 'name': name, 'country': country}

        dp_resp = requests.get('http://realnexus.comit.cloud:5000/api/Ports/DestinationPorts', headers=headers, timeout=5)
        if dp_resp.status_code == 200:
            for p in dp_resp.json():
                code = (p.get('code') or p.get('unlocode') or p.get('locode') or '').strip()
                name = (p.get('name') or p.get('portName') or code).strip()
                country = (p.get('country') or p.get('countryName') or '').strip()
                if code and name:
                    if code not in all_ports_dict or not all_ports_dict[code]['name']:
                        all_ports_dict[code] = {'code': code, 'name': name, 'country': country}
    except Exception as e:
        print(f"Error fetching live ports list: {e}")

    ports_list = sorted(list(all_ports_dict.values()), key=lambda x: x['name'])
    result = {'origins': ports_list, 'destinations': ports_list}
    if ports_list:
        _PORTS_LIST_CACHE['data'] = result
        _PORTS_LIST_CACHE['expires_at'] = now + 3600  # 1 hour cache
    return jsonify(result)




