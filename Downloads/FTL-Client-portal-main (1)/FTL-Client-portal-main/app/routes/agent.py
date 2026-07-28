from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.models import EdiPreAlert, Booking
from app.services.edi_parser import EdiParser
from app.services.email_service import EmailService
from app.services.ai_extractor import AiExtractor
from app import db
import os

agent_bp = Blueprint('agent', __name__)

def agent_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['agent', 'admin']:
            flash('Agent access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@agent_bp.route('/dashboard')
@login_required
@agent_required
def dashboard():
    # Show only EDIs the agent might be interested in (or all for now)
    edis = EdiPreAlert.query.order_by(EdiPreAlert.created_at.desc()).all()
    email_connected = current_user.email_token is not None
    return render_template('agent/dashboard.html', edis=edis, email_connected=email_connected)

@agent_bp.route('/sync')
@login_required
@agent_required
def sync_email():
    result = EmailService.sync_edi_emails(current_user)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Sync failed: {result['message']}", 'danger')
    return redirect(url_for('agent.dashboard'))

@agent_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@agent_required
def upload_edi():
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            flash('No files selected.', 'danger')
            return redirect(request.url)
        
        success_count = 0
        fail_count = 0
        
        for file in files:
            if not file.filename: continue
            
            try:
                content_bytes = file.read()
                
                # Use AI to extract structured data from bytes
                ai_result = AiExtractor.extract_edi_data(content_bytes, file.filename)
                
                if ai_result['success']:
                    payload = ai_result['data']
                    result = EdiParser.parse_payload(payload, source_type=f'AI Upload ({file.filename})')
                    if result['success']:
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                    print(f"AI Error for {file.filename}: {ai_result['message']}")
                    
            except Exception as e:
                fail_count += 1
                print(f"Processing Error for {file.filename}: {str(e)}")
        
        if success_count > 0:
            flash(f'Successfully processed {success_count} files via Gemini AI.', 'success')
        if fail_count > 0:
            flash(f'Failed to process {fail_count} files. Check logs for details.', 'danger')
            
        return redirect(url_for('agent.dashboard'))
            
    return render_template('agent/upload.html')
