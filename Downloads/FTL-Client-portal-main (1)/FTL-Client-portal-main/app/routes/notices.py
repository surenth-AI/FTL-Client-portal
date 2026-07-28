from flask import Blueprint, render_template, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.models.models import Booking, ArrivalNotice
from app.services.notice_service import NoticeService
import os

notices = Blueprint('notices', __name__)

@notices.route('/generate/<int:booking_id>')
@login_required
def generate(booking_id):
    """
    Trigger Arrival Notice generation for a booking.
    """
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    results = NoticeService.send_multi_party_notices(booking)
    
    success_count = sum(1 for r in results if r['success'])
    flash(f'Generated {success_count} arrival notices.', 'success')
    return redirect(url_for('admin.shipment_details', id=booking_id))

@notices.route('/view/<int:notice_id>')
@login_required
def view_pdf(notice_id):
    """
    View the generated Arrival Notice PDF.
    """
    notice = ArrivalNotice.query.get_or_404(notice_id)
    
    # Permission check: Admin or the customer who owns the booking
    if current_user.role != 'admin' and notice.booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if not notice.pdf_path or not os.path.exists(notice.pdf_path):
        flash('PDF not found.', 'danger')
        return redirect(url_for('customer.view_booking', id=notice.booking_id))
    
    return send_file(os.path.abspath(notice.pdf_path), mimetype='application/pdf')
