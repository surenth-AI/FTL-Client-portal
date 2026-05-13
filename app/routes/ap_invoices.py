from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app.models.models import db, VendorInvoice, VendorInvoiceItem

ap_invoices_bp = Blueprint('ap_invoices', __name__, url_prefix='/ap-invoices')

@ap_invoices_bp.route('/')
@login_required
def list_invoices():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    query = VendorInvoice.query.filter_by(user_id=current_user.id)
    
    if q:
        query = query.filter(db.or_(
            VendorInvoice.supplier.ilike(f'%{q}%'),
            VendorInvoice.invoice_number.ilike(f'%{q}%')
        ))
    if status:
        query = query.filter(VendorInvoice.match_status.ilike(f'%{status}%'))
        
    pagination = query.order_by(VendorInvoice.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('ap_invoices/list.html', 
                           invoices=pagination.items, 
                           pagination=pagination, q=q, status=status)

@ap_invoices_bp.route('/<int:inv_id>')
@login_required
def detail(inv_id):
    inv = VendorInvoice.query.get_or_404(inv_id)
    if inv.user_id != current_user.id:
        return "Unauthorized", 403
        
    items_total = sum(item.total_price for item in inv.items) if inv.items else 0
    delta = abs((inv.amount or 0) - items_total)
    math_verified = delta < 0.01
    
    intelligence = {
        'items_total': items_total,
        'delta': delta,
        'math_verified': math_verified,
        'global_refs': {},
        'distributed_refs': []
    }
    return render_template('ap_invoices/detail.html', inv=inv, intelligence=intelligence)

@ap_invoices_bp.route('/upload-ai', methods=['POST'])
@login_required
def upload_ai():
    if 'pdf_file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('ap_invoices.list_invoices'))
    
    file = request.files['pdf_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('ap_invoices.list_invoices'))

    if file and file.filename.endswith('.pdf'):
        try:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)

            with open(filepath, "rb") as f:
                file_data = f.read()

            from app.services.ai_invoice_service import parse_invoice_document, verify_invoice_match
            from app.models.models import VendorInvoiceReference
            
            data = parse_invoice_document(file_data, "application/pdf")
            
            total_float = 0.0
            try:
                raw_total = data.get('total_amount')
                clean_total = str(raw_total).replace('$', '').replace('€', '').replace(',', '').strip()
                total_float = float(clean_total)
            except: pass

            new_inv = VendorInvoice(
                supplier=data.get('vendor_name', 'Unknown Vendor'),
                supplier_code=data.get('supplier_code'),
                invoice_number=data.get('invoice_number', 'UNKNOWN'),
                invoice_type=data.get('invoice_type', 'Invoice'),
                amount=total_float,
                currency=data.get('currency', 'EUR'),
                user_id=current_user.id,
                pdf_path=filepath
            )
            
            status, matched_job_id = verify_invoice_match(new_inv, data)
            new_inv.match_status = status
            new_inv.matched_job_id = matched_job_id
            
            db.session.add(new_inv)
            db.session.flush()

            for it in data.get('line_items', []):
                t_price = 0.0
                try: t_price = float(str(it.get('total_price', 0)).replace(',', '').strip())
                except: pass
                
                new_item = VendorInvoiceItem(
                    invoice_id=new_inv.id,
                    description=it.get('description', 'Unknown Item'),
                    total_price=t_price,
                    charge_code=it.get('charge_code'),
                    vendor_name=it.get('vendor_name'),
                    job_id=it.get('job_id')
                )
                db.session.add(new_item)
                
            db.session.commit()
            flash(f"AI Success! Extracted invoice for {new_inv.supplier} (${new_inv.amount}).", "success")
            return redirect(url_for('ap_invoices.detail', inv_id=new_inv.id))
            
        except Exception as e:
            flash(f"AI Parsing Error: {str(e)}", "error")
    else:
        flash("Only PDF files are supported for AI Extraction.", "error")
        
    return redirect(url_for('ap_invoices.list_invoices'))

@ap_invoices_bp.route('/manual-upload', methods=['POST'])
@login_required
def manual_upload():
    if 'pdf_file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('ap_invoices.list_invoices'))
    
    file = request.files['pdf_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('ap_invoices.list_invoices'))

    if file and file.filename.endswith('.pdf'):
        try:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)

            supplier = request.form.get('supplier', 'Manual Entry')
            amount = request.form.get('amount', 0.0)
            inv_no = request.form.get('invoice_number', 'PENDING')

            new_inv = VendorInvoice(
                supplier=supplier,
                invoice_number=inv_no,
                amount=float(amount),
                match_status="PENDING MANUAL REVIEW",
                user_id=current_user.id,
                pdf_path=filepath
            )
            db.session.add(new_inv)
            db.session.commit()
            flash(f"Manual invoice created successfully.", "success")
            return redirect(url_for('ap_invoices.detail', inv_id=new_inv.id))
        except Exception as e:
            flash(f"Upload Error: {str(e)}", "error")
    else:
        flash("Only PDF files are supported.", "error")
        
    return redirect(url_for('ap_invoices.list_invoices'))

@ap_invoices_bp.route('/download/<int:inv_id>')
@login_required
def download_pdf(inv_id):
    inv = VendorInvoice.query.get_or_404(inv_id)
    if inv.user_id != current_user.id:
        return "Unauthorized", 403
    if not inv.pdf_path or not os.path.exists(inv.pdf_path):
        return "File not found", 404
    return send_file(inv.pdf_path, as_attachment=False)
