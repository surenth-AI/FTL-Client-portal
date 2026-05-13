from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.models import Rate, Booking, TrackingEvent, User, Company
from app.services.excel_importer import ExcelImporter
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

def get_bi_analytics():
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
        return {
            'metrics': {'total_cbm': round(total_cbm, 2), 'total_wgt': round(total_wgt, 2), 'avg_cbm': round(avg_cbm, 2), 'hazmat_ratio': round(hazmat_ratio, 1), 'invoice_issues': int(df['INCO'].isna().sum()), 'bl_issues': int(df['FileID'].isna().sum())},
            'charts': {
                'customers': {'labels': customers.index.tolist(), 'data': customers.values.tolist()},
                'origins': {'labels': df.groupby('POL').size().nlargest(5).index.tolist(), 'data': df.groupby('POL').size().nlargest(5).values.tolist()},
                'dests': {'labels': df.groupby('POD').size().nlargest(5).index.tolist(), 'data': df.groupby('POD').size().nlargest(5).values.tolist()},
                'traffic': {'labels': df.groupby('TRAFFIC').size().index.tolist(), 'data': df.groupby('TRAFFIC').size().values.tolist()}
            }
        }
    except Exception as e:
        return fallback_bi

# --- Routes ---

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_bookings = Booking.query.count()
    total_customers = User.query.filter_by(role='customer', status='active').count()
    total_companies = Company.query.filter_by(status='active').count()
    total_staff = User.query.filter(User.role != 'customer').count()
    total_rates = Rate.query.count()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    all_customers = User.query.filter_by(role='customer', status='active').all()
    
    return render_template('admin/dashboard.html', 
                         total_bookings=total_bookings, 
                         total_customers=total_customers,
                         total_companies=total_companies,
                         total_staff=total_staff,
                         total_rates=total_rates,
                         recent_bookings=recent_bookings,
                         all_customers=all_customers)

@admin.route('/users')
@admin_required
@super_admin_required
def manage_users():
    staff = User.query.filter(User.role != 'customer').all()
    customers = User.query.filter_by(role='customer').all()
    return render_template('admin/manage_users.html', staff=staff, customers=customers)

@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
@super_admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.role = request.form.get('role')
        user.department = request.form.get('department') if user.role == 'operation_executive' else None
        db.session.commit()
        flash(f'User {user.name} updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', user=user)


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

@admin.route('/rates')
@admin_required
def view_rates():
    page = request.args.get('page', 1, type=int)
    pagination = Rate.query.order_by(Rate.id.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template('admin/rates.html', pagination=pagination, rates=pagination.items)

@admin.route('/rates/upload', methods=['GET', 'POST'])
@admin_required
def upload_rates():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        filename = file.filename.lower()
        try:
            if filename.endswith('.xlsx'):
                result = ExcelImporter.process_file(file.read(), filename)
                if result['success']:
                    flash(result['message'], 'success')
                    return redirect(url_for('admin.view_rates'))
                flash(f"Excel error: {result['message']}", "danger")
            else:
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.DictReader(stream)
                for row in csv_input:
                    db.session.add(Rate(origin=row['origin'], destination=row['destination'], nvocc_name=row['nvocc_name'], base_rate=float(row['base_rate']), surcharges=float(row['surcharges']), transit_days=int(row['transit_days']), validity_start=datetime.strptime(row['validity_start'], '%Y-%m-%d').date(), validity_end=datetime.strptime(row['validity_end'], '%Y-%m-%d').date()))
                db.session.commit()
                flash('Successfully uploaded rates.', 'success')
                return redirect(url_for('admin.view_rates'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'danger')
    return render_template('admin/upload.html')

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

@admin.route('/rate/delete/<int:rate_id>')
@admin_required
def delete_rate(rate_id):
    db.session.delete(Rate.query.get_or_404(rate_id))
    db.session.commit()
    flash('Rate deleted.', 'success')
    return redirect(url_for('admin.view_rates'))

@admin.route('/rates/clear')
@admin_required
def clear_rates():
    Rate.query.delete()
    db.session.commit()
    flash('All rates cleared.', 'success')
    return redirect(url_for('admin.view_rates'))

@admin.route('/create-user', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(request.url)
        role = request.form.get('role', 'customer')
        new_user = User(name=request.form.get('name'), email=email, password_hash=generate_password_hash(request.form.get('password')), role=role, department=request.form.get('department') if role == 'operation_executive' else None, status='active')
        db.session.add(new_user)
        db.session.commit()
        flash(f'User created successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_user.html')

@admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if current_user.role not in ['super_admin', 'admin']:
        flash('Access denied. Administrator role required.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    from app.models.models import SystemSetting
    import os
    from werkzeug.utils import secure_filename
    
    sys_settings = SystemSetting.query.first()
    if not sys_settings:
        sys_settings = SystemSetting(theme_color='blue', logo_path='img/logo.png')
        db.session.add(sys_settings)
        db.session.commit()
        
    if request.method == 'POST':
        theme_color = request.form.get('theme_color')
        logo_file = request.files.get('logo_file')
        banner_file = request.files.get('banner_file')
        default_layout = request.form.get('default_layout')
        
        if theme_color:
            sys_settings.theme_color = theme_color
            
        if default_layout:
            sys_settings.default_layout = default_layout
            
        static_img_dir = os.path.join(current_app.root_path, 'static', 'img')
        if not os.path.exists(static_img_dir):
            os.makedirs(static_img_dir)

        # Handle Organization Logo Upload
        if logo_file and logo_file.filename != '':
            filename = secure_filename(logo_file.filename)
            save_path = os.path.join(static_img_dir, filename)
            logo_file.save(save_path)
            sys_settings.logo_path = 'img/' + filename
            
        # Handle Login Panel Banner Upload
        if banner_file and banner_file.filename != '':
            filename = secure_filename(banner_file.filename)
            save_path = os.path.join(static_img_dir, filename)
            banner_file.save(save_path)
            sys_settings.login_banner_path = 'img/' + filename
            
        db.session.commit()
        flash('System settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    return render_template('admin/settings.html', settings=sys_settings)

