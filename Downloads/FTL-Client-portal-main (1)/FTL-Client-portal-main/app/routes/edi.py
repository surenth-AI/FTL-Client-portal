from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.edi_parser import EdiParser
from app.models.models import EdiPreAlert, Booking, ArrivalNotice
from app import db
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
import os

edi = Blueprint('edi', __name__)

@edi.route('/ingest', methods=['POST'])
def ingest():
    """
    API Endpoint for EDI ingestion.
    Expects JSON payload.
    """
    payload = request.get_json()
    if not payload:
        return jsonify({"success": False, "message": "No JSON payload provided"}), 400
    
    result = EdiParser.parse_payload(payload, source_type='API')
    return jsonify(result)

@edi.route('/admin/dashboard')
@login_required
def dashboard():
    """
    Admin view to see all incoming EDI pre-alerts.
    """
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    pre_alerts = EdiPreAlert.query.order_by(EdiPreAlert.created_at.desc()).all()
    email_connected = current_user.email_token is not None
    return render_template('edi/dashboard.html', pre_alerts=pre_alerts, email_connected=email_connected)

@edi.route('/admin/sync')
@login_required
def sync_email():
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    result = EmailService.sync_edi_emails(current_user)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Sync failed: {result['message']}", 'danger')
    return redirect(url_for('edi.dashboard'))

@edi.route('/send-notices/<int:id>')
@login_required
def send_notices(id):
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('index'))
    
    result = NotificationService.notify_all_parties(id)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Error: {result['message']}", 'danger')
    return redirect(url_for('edi.dashboard'))

@edi.route('/admin/retry/<int:id>')
@login_required
def retry(id):
    """
    Retry parsing/booking creation for a quarantined EDI.
    """
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    pre_alert = EdiPreAlert.query.get_or_404(id)
    result = EdiParser._auto_create_booking(pre_alert)
    
    if result['success']:
        pre_alert.booking_id = result['booking_id']
        pre_alert.parse_status = 'parsed'
        db.session.commit()
        flash('Booking successfully created from EDI.', 'success')
    else:
        flash(f'Retry failed: {result["message"]}', 'danger')
        
    return redirect(url_for('edi.dashboard'))
