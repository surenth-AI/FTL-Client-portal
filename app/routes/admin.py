from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.models import Booking, TrackingEvent, User, Company
from app.services.excel_importer import ExcelImporter
from app.utils import validate_password_strength
from app import db
import csv
import io
from datetime import datetime
from functools import wraps
import pandas as pd

admin = Blueprint('admin', __name__)

# --- Access Control Decorators ---

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['super_admin', 'admin', 'operation_executive']:
            flash('Staff access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            flash('Super Admin access required.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def department_required(departments):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role in ['super_admin', 'admin']:
                return f(*args, **kwargs)
            if current_user.department in departments:
                return f(*args, **kwargs)
            flash(f'Access denied. Requires department: {", ".join(departments)}', 'danger')
            return redirect(url_for('admin.dashboard'))
        return decorated_function
    return decorator

# --- Analytics Helpers ---

_bi_cache = {
    'data': None,
    'expires_at': 0
}

def get_bi_analytics():
    import time
    now = time.time()
    if _bi_cache['data'] is not None and now < _bi_cache['expires_at']:
        return _bi_cache['data']

    excel_path = r'D:\AXE Global\sevenlogs-Demo S1\Sample csv\BI Data\FMSBKG-20260413035735392.xls'
    fallback_bi = {
        'metrics': {'total_cbm': 4250.75, 'total_wgt': 125400.0, 'avg_cbm': 12.4, 'hazmat_ratio': 8.5, 'invoice_issues': 12, 'bl_issues': 5},
        'charts': {
            'customers': {'labels': ['Global SA', 'TechStream', 'Nordic', 'Asia', 'EuroTrans'], 'data': [1200, 950, 780, 620, 450]},
            'origins': {'labels': ['Shanghai', 'Hamburg', 'Rotterdam', 'Jebel Ali', 'Singapore'], 'data': [45, 32, 28, 22, 18]},
            'dests': {'labels': ['New York', 'Felixstowe', 'Mumbai', 'Sydney', 'Santos'], 'data': [38, 30, 25, 20, 15]},
            'traffic': {'labels': ['EXPORT', 'IMPORT', 'CROSS-TRADE'], 'data': [65, 25, 10]}
        }
    }
    try:
        df = pd.read_excel(excel_path)
        total_cbm = float(df['CBM'].sum())
        total_wgt = float(df['Wgt'].sum())
        avg_cbm = float(df['CBM'].mean())
        hazmat_count = int(df[df['IsHazmat'] == True].shape[0])
        hazmat_ratio = (hazmat_count / df.shape[0]) * 100 if df.shape[0] > 0 else 0
        customers = df.groupby('CUSTOMER')['CBM'].sum().nlargest(10)
        
        result = {
            'metrics': {'total_cbm': round(total_cbm, 2), 'total_wgt': round(total_wgt, 2), 'avg_cbm': round(avg_cbm, 2), 'hazmat_ratio': round(hazmat_ratio, 1), 'invoice_issues': int(df['INCO'].isna().sum()), 'bl_issues': int(df['FileID'].isna().sum())},
            'charts': {
                'customers': {'labels': customers.index.tolist(), 'data': customers.values.tolist()},
                'origins': {'labels': df.groupby('POL').size().nlargest(5).index.tolist(), 'data': df.groupby('POL').size().nlargest(5).values.tolist()},
                'dests': {'labels': df.groupby('POD').size().nlargest(5).index.tolist(), 'data': df.groupby('POD').size().nlargest(5).values.tolist()},
                'traffic': {'labels': df.groupby('TRAFFIC').size().index.tolist(), 'data': df.groupby('TRAFFIC').size().values.tolist()}
            }
        }
    except Exception as e:
        result = fallback_bi

    _bi_cache['data'] = result
    _bi_cache['expires_at'] = now + 600  # cache for 10 minutes
    return result

# --- Routes ---

@admin.route('/dashboard')
@admin_required
def dashboard():
    from sqlalchemy.orm import joinedload
    total_bookings = Booking.query.count()
    total_customers = User.query.filter_by(role='customer', status='active').count()
    total_companies = Company.query.filter_by(status='active').count()
    total_staff = User.query.filter(User.role != 'customer').count()
    recent_bookings = Booking.query.options(joinedload(Booking.customer).joinedload(User.company)).order_by(Booking.created_at.desc()).limit(10).all()
    all_customers = User.query.filter_by(role='customer', status='active').all()
    
    return render_template('admin/dashboard.html', 
                         total_bookings=total_bookings, 
                         total_customers=total_customers,
                         total_companies=total_companies,
                         total_staff=total_staff,
                         recent_bookings=recent_bookings,
                         all_customers=all_customers)

@admin.route('/users')
@admin_required
def manage_users():
    from sqlalchemy.orm import joinedload
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    q = request.args.get('q', '', type=str)
    
    query = User.query.options(joinedload(User.company)).filter_by(role='customer')
    if q:
        search = f"%{q}%"
        query = query.filter((User.name.ilike(search)) | (User.email.ilike(search)))
        
    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    if current_user.role == 'super_admin':
        staff = User.query.options(joinedload(User.company)).filter(User.role != 'customer').all()
    else:
        staff = []
        
    return render_template('admin/manage_users.html', staff=staff, customers=pagination.items, pagination=pagination, q=q)

@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
@super_admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.role = request.form.get('role')
        user.mobile = request.form.get('mobile') or None
        user.status = request.form.get('status', user.status)
        user.department = request.form.get('department') if user.role == 'operation_executive' else None
        erp_code = request.form.get('erp_customer_code', '').strip()
        if erp_code:
            user.erp_customer_code = erp_code
        db.session.commit()
        flash(f'User {user.name} updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', user=user)



@admin.route('/user/create', methods=['GET', 'POST'])
@admin_required
@super_admin_required
def create_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        department = request.form.get('department') if role == 'operation_executive' else None

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered.', 'danger')
            return render_template('admin/create_user.html')

        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            role=role,
            department=department,
            status='active'
        )
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {name} created successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/create_user.html')



@admin.route('/shipment-intelligence')
@admin_required
def shipment_intelligence():
    from sqlalchemy import func
    from app.models.models import ProformaInvoice, Invoice, EdiPreAlert
    
    bi_data = get_bi_analytics()
    total_bookings = Booking.query.count()
    pending_shipments = Booking.query.filter(Booking.status.in_(['Booked', 'Pending Review'])).count()
    
    # Milestone Distribution
    status_counts = db.session.query(Booking.status, func.count(Booking.id)).group_by(Booking.status).all()
    milestone_dist = {
        'labels': [s[0] for s in status_counts],
        'data': [s[1] for s in status_counts]
    }
    
    # --- New Financial Intelligence ---
    unpaid_total = db.session.query(func.sum(ProformaInvoice.total_amount)).filter(ProformaInvoice.payment_status == 'UNPAID').scalar() or 0
    paid_total = db.session.query(func.sum(Invoice.total_amount)).scalar() or 0
    total_revenue = float(unpaid_total) + float(paid_total)
    collection_rate = (float(paid_total) / total_revenue * 100) if total_revenue > 0 else 0
    
    revenue_metrics = {
        'total': round(total_revenue, 2),
        'paid': round(float(paid_total), 2),
        'pending': round(float(unpaid_total), 2),
        'rate': round(collection_rate, 1)
    }

    # --- New EDI Intelligence ---
    total_edi = EdiPreAlert.query.count()
    parsed_edi = EdiPreAlert.query.filter_by(parse_status='parsed').count()
    edi_efficiency = (parsed_edi / total_edi * 100) if total_edi > 0 else 0
    
    # --- Document Release Velocity ---
    # Proformas vs Released Invoices
    proforma_count = ProformaInvoice.query.count()
    released_count = Invoice.query.count()
    release_ratio = (released_count / proforma_count * 100) if proforma_count > 0 else 0

    return render_template('admin/shipment_intelligence.html', 
                         bi=bi_data,
                         total_bookings=total_bookings,
                         pending_shipments=pending_shipments,
                         milestones=milestone_dist,
                         revenue=revenue_metrics,
                         edi_stats={
                             'total': total_edi,
                             'parsed': parsed_edi,
                             'efficiency': round(edi_efficiency, 1)
                         },
                         release_stats={
                             'proformas': proforma_count,
                             'released': released_count,
                             'ratio': round(release_ratio, 1)
                         })


@admin.route('/booking/<int:booking_id>/update', methods=['GET', 'POST'])
@admin_required
def update_tracking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if request.method == 'POST':
        new_status = request.form.get('status')
        booking.status = new_status
        db.session.add(TrackingEvent(booking_id=booking.id, status=new_status, location=request.form.get('location')))
        db.session.commit()
        flash('Tracking updated successfully.', 'success')
        return redirect(url_for('admin.shipment_details', id=booking_id))
    return render_template('admin/tracking_update.html', booking=booking)

@admin.route('/shipment/<int:id>')
@admin_required
def shipment_details(id):
    booking = Booking.query.get_or_404(id)
    return render_template('admin/shipment_details.html', booking=booking)


# --- System Settings ---

SETTINGS_SECTIONS = {
    'branding': 'admin/settings/branding.html',
    'appearance': 'admin/settings/appearance.html',
    'mail': 'admin/settings/mail.html',
}
ADMIN_ONLY_SECTIONS = {'branding', 'mail'}
ALLOWED_LOGO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}
ALLOWED_BANNER_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def _is_settings_admin():
    return current_user.role in ['super_admin', 'admin']


def _get_system_settings():
    from app.models.models import SystemSetting
    sys_settings = SystemSetting.query.first()
    if not sys_settings:
        sys_settings = SystemSetting(theme_color='blue', logo_path='img/logo.png', default_layout='sidebar', typography='Inter')
        db.session.add(sys_settings)
        db.session.commit()
    return sys_settings


def _commit_settings(message):
    db.session.commit()
    # Invalidate system settings cache
    try:
        from app import clear_settings_cache
        clear_settings_cache()
    except Exception as e:
        current_app.logger.warning(f"Failed to clear settings cache: {e}")
    flash(message, 'success')


def _save_uploaded_image(file_storage, allowed_extensions):
    """Save an uploaded image into static/img and return its static-relative path.
    Returns None when no file was sent; raises ValueError on a disallowed type."""
    import os
    from werkzeug.utils import secure_filename

    if not file_storage or file_storage.filename == '':
        return None
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported file type. Allowed: {', '.join(sorted(allowed_extensions)).upper()}")

    static_img_dir = os.path.join(current_app.root_path, 'static', 'img')
    os.makedirs(static_img_dir, exist_ok=True)
    file_storage.save(os.path.join(static_img_dir, filename))
    return 'img/' + filename


def _save_appearance(sys_settings):
    theme_color = request.form.get('theme_color')
    typography = request.form.get('typography')
    default_layout = request.form.get('default_layout')

    if theme_color:
        sys_settings.theme_color = theme_color
    if typography:
        sys_settings.typography = typography
    if default_layout in ('sidebar', 'topbar'):
        sys_settings.default_layout = default_layout


def _save_branding(sys_settings):
    logo_path = _save_uploaded_image(request.files.get('logo_file'), ALLOWED_LOGO_EXTENSIONS)
    if logo_path:
        sys_settings.logo_path = logo_path

    banner_path = _save_uploaded_image(request.files.get('banner_file'), ALLOWED_BANNER_EXTENSIONS)
    if banner_path:
        sys_settings.login_banner_path = banner_path

    sys_settings.terms_conditions_url = request.form.get('terms_conditions_url', '').strip() or None


def _save_mail(sys_settings):
    sys_settings.smtp_server = request.form.get('smtp_server', '').strip() or None

    smtp_port = request.form.get('smtp_port', '').strip()
    sys_settings.smtp_port = int(smtp_port) if smtp_port.isdigit() else 587

    sys_settings.smtp_user = request.form.get('smtp_user', '').strip() or None

    # Only update password if a new one is provided (so we don't overwrite with blanks)
    smtp_pw = request.form.get('smtp_password')
    if smtp_pw and smtp_pw.strip() != '':
        sys_settings.smtp_password = smtp_pw

    sys_settings.receiver_email = request.form.get('receiver_email', '').strip() or None


@admin.route('/settings', defaults={'section': None}, methods=['GET', 'POST'])
@admin.route('/settings/<section>', methods=['GET', 'POST'])
@login_required
def settings(section):
    is_admin = _is_settings_admin()
    if section not in SETTINGS_SECTIONS or (section in ADMIN_ONLY_SECTIONS and not is_admin):
        return redirect(url_for('admin.settings', section='branding' if is_admin else 'appearance'))

    sys_settings = _get_system_settings()

    if request.method == 'POST':
        try:
            if section == 'appearance':
                _save_appearance(sys_settings)
            elif section == 'branding':
                _save_branding(sys_settings)
            elif section == 'mail':
                _save_mail(sys_settings)
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
            return redirect(url_for('admin.settings', section=section))

        _commit_settings('Settings updated successfully.')
        return redirect(url_for('admin.settings', section=section))

    return render_template(SETTINGS_SECTIONS[section], settings=sys_settings, section=section, is_admin=is_admin)


@admin.route('/field-config', methods=['GET', 'POST'])
@login_required
def field_config():
    if not _is_settings_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('admin.settings'))

    sys_settings = _get_system_settings()

    if request.method == 'POST':
        import json
        # Incoterm rules arrive as a JSON string built by the rules editor
        incoterm_rules_str = request.form.get('incoterm_rules')
        if incoterm_rules_str:
            try:
                rules = json.loads(incoterm_rules_str)
            except json.JSONDecodeError:
                flash('Invalid JSON provided for Incoterm Rules.', 'danger')
                return redirect(url_for('admin.field_config'))
            if not isinstance(rules, dict) or not isinstance(rules.get('rules', []), list):
                flash('Invalid structure provided for Incoterm Rules.', 'danger')
                return redirect(url_for('admin.field_config'))
            sys_settings.incoterm_rules = rules if rules.get('rules') else None
        else:
            sys_settings.incoterm_rules = None

        _commit_settings('Field configuration updated successfully.')
        return redirect(url_for('admin.field_config'))

    return render_template('admin/field_config.html', settings=sys_settings)
