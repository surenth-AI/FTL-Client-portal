from flask import Blueprint, render_template, flash, redirect, url_for, request, send_file
from flask_login import login_required, current_user
from app.models.models import Booking, ProformaInvoice, Invoice
from app.services.billing_service import BillingService
from app.services.notification_service import NotificationService
from app import db
import os

billing = Blueprint('billing', __name__)

@billing.route('/admin/manage')
@login_required
def manage():
    """
    Admin view for managing all invoices and payments.
    """
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    unpaid_proformas = ProformaInvoice.query.filter_by(payment_status='UNPAID').all() or []
    recent_invoices = Invoice.query.order_by(Invoice.issued_at.desc()).limit(20).all() or []
    
    # Pre-calculate totals for the dashboard with safety defaults
    total_unpaid = sum(float(p.total_amount or 0) for p in unpaid_proformas)
    total_collected = sum(float(i.total_amount or 0) for i in recent_invoices)
    
    return render_template('billing/manage.html', 
                           unpaid=unpaid_proformas, 
                           invoices=recent_invoices,
                           total_unpaid=total_unpaid,
                           total_collected=total_collected)

@billing.route('/issue_proforma/<int:booking_id>')
@login_required
def issue_proforma(booking_id):
    """
    Issue a new Proforma Invoice for a booking.
    """
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    result = BillingService.create_proforma(booking)
    
    if result['success']:
        flash('Proforma Invoice issued successfully.', 'success')
    else:
        flash(f'Error: {result["message"]}', 'danger')
        
    return redirect(url_for('admin.shipment_details', id=booking_id))

@billing.route('/confirm_payment/<int:proforma_id>', methods=['POST'])
@login_required
def confirm_payment(proforma_id):
    """
    Admin confirms receipt of payment.
    """
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    proforma = ProformaInvoice.query.get_or_404(proforma_id)
    payment_ref = request.form.get('payment_ref')
    
    if not payment_ref:
        flash('Payment reference is required.', 'warning')
        return redirect(url_for('billing.manage'))
        
    result = BillingService.confirm_payment(proforma, payment_ref, current_user.id)
    
    if result['success']:
        flash(f'Payment confirmed. Final Invoice {result["invoice_number"]} issued and B/L released.', 'success')
    else:
        flash(f'Error: {result["message"]}', 'danger')
        
    return redirect(url_for('billing.manage'))

@billing.route('/view_proforma/<int:id>')
@login_required
def view_proforma(id):
    """
    View Proforma details (and potentially render PDF).
    """
    proforma = ProformaInvoice.query.get_or_404(id)
    if current_user.role != 'admin' and proforma.booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
        
    return render_template('billing/proforma_view.html', proforma=proforma)

@billing.route('/view_invoice/<int:id>')
@login_required
def view_invoice(id):
    """
    View Final Tax Invoice details.
    """
    invoice = Invoice.query.get_or_404(id)
    if current_user.role != 'admin' and invoice.booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
        
    return render_template('billing/invoice_view.html', invoice=invoice)

@billing.route('/download_invoice/<int:id>')
@login_required
def download_invoice(id):
    """
    Generate and download a professional Tax Invoice PDF.
    """
    invoice = Invoice.query.get_or_404(id)
    if current_user.role != 'admin' and invoice.booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    pdf_path = NotificationService.generate_invoice_pdf(invoice)
    if pdf_path and os.path.exists(pdf_path):
        return send_file(os.path.abspath(pdf_path), as_attachment=True)
    else:
        flash('Could not generate invoice PDF.', 'danger')
        return redirect(request.referrer or url_for('index'))

@billing.route('/download_proforma/<int:id>')
@login_required
def download_proforma(id):
    """
    Generate and download a professional Proforma PDF.
    """
    proforma = ProformaInvoice.query.get_or_404(id)
    if current_user.role != 'admin' and proforma.booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    pdf_path = NotificationService.generate_proforma_pdf(proforma)
    if pdf_path and os.path.exists(pdf_path):
        return send_file(os.path.abspath(pdf_path), as_attachment=True)
    else:
        flash('Could not generate proforma PDF.', 'danger')
        return redirect(request.referrer or url_for('index'))

@billing.route('/download_do/<int:booking_id>')
@login_required
def download_do(booking_id):
    """
    Generate and download the Delivery Order (Cargo Release).
    """
    booking = Booking.query.get_or_404(booking_id)
    if current_user.role != 'admin' and booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if booking.payment_status != 'CONFIRMED':
        flash('Cargo not yet released. Please settle payment.', 'warning')
        return redirect(url_for('index'))
    
    pdf_path = NotificationService.generate_delivery_order_pdf(booking)
    if pdf_path and os.path.exists(pdf_path):
        return send_file(os.path.abspath(pdf_path), as_attachment=True)
    else:
        flash('Could not generate Delivery Order.', 'danger')
        return redirect(request.referrer or url_for('index'))
