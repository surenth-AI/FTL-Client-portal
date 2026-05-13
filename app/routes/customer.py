from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from app.models.models import Rate, Booking, TrackingEvent, CargoItem, BookingAttachment, ShippingInstruction
from app.services.rate_engine import RateEngine
from app import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

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
                quantity=int(qty_list[i]) if qty_list[i] else 0,
                package_type=type_list[i],
                weight_kg=float(weight_list[i]) if weight_list[i] else 0.0,
                volume_cbm=float(vol_list[i]) if vol_list[i] else 0.0,
                length=float(l_list[i]) if l_list[i] else 0.0,
                width=float(w_list[i]) if w_list[i] else 0.0,
                height=float(h_list[i]) if h_list[i] else 0.0,
                uom=uom_list[i],
                hs_code=hs_list[i],
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
                container_count=int(c_qty_list[i]) if c_qty_list[i] else 0,
                container_type=c_type_list[i],
                quantity=int(p_qty_list[i]) if p_qty_list[i] else 0,
                package_type=p_type_list[i],
                volume_cbm=float(vol_list[i]) if i < len(vol_list) and vol_list[i] else 0.0,
                weight_kg=float(weight_list[i]) if weight_list[i] else 0.0,
                hs_code=hs_list[i],
                description=desc_list[i] if i < len(desc_list) else None,
                is_imo=True if i < len(is_imo_list) and is_imo_list[i] == 'yes' else False,
                un_number=un_list[i] if i < len(un_list) else None,
                packing_group=pg_list[i] if i < len(pg_list) else None,
                imo_class=class_list[i] if i < len(class_list) else None
            )
            db.session.add(item)

@customer.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    recent_shipments = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).limit(3).all()
    total_active = Booking.query.filter_by(user_id=current_user.id).filter(Booking.status != 'Delivered').count()
    
    # Get unique origins and destinations for the quick search form
    origins = db.session.query(Rate.origin).distinct().all()
    destinations = db.session.query(Rate.destination).distinct().all()
    
    return render_template('customer/dashboard.html', 
                         recent_shipments=recent_shipments,
                         total_active=total_active,
                         origins=[o[0] for o in origins if o], 
                         destinations=[d[0] for d in destinations if d])

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
        
    # Get unique origins and destinations for the search form
    origins = db.session.query(Rate.origin).distinct().all()
    destinations = db.session.query(Rate.destination).distinct().all()
    
    return render_template('customer/new_booking.html', 
                         origins=[o[0] for o in origins], 
                         destinations=[d[0] for d in destinations],
                         query=session.get('search_query', {}))

@customer.route('/rate-results')
@login_required
def rate_results():
    query = session.get('search_query')
    if not query:
        return redirect(url_for('customer.new_booking'))
        
    rates = Rate.query.filter_by(
        origin=query['origin'], 
        destination=query['destination'],
        service_type=query['service_type']
    ).all()
    results = RateEngine.calculate_ranks(rates, query['volume'])
    
    return render_template('customer/rate_results.html', results=results, query=query)

@customer.route('/finalize-booking', methods=['POST'])
@login_required
def finalize_booking():
    if current_user.role != 'customer':
        flash('Agents and Administrators cannot place bookings directly.', 'warning')
        return redirect(url_for('customer.rate_results'))
    rate_id = request.form.get('rate_id')
    raw_volume = request.form.get('volume')
    volume = float(raw_volume) if raw_volume else 0.0
    total_cost = float(request.form.get('total_cost'))
    service_type = request.form.get('service_type')
    
    rate = Rate.query.get_or_404(rate_id)
    
    query = session.get('search_query', {})
    
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
        status='Booked'
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
        status='Pending Review'
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
    
    flash('Booking request submitted successfully! Our team will review it shortly.', 'success')
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

