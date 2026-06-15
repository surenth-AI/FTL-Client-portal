from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flasgger import Swagger
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
swagger = Swagger()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    swagger.init_app(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    with app.app_context():
        from app.models import models
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Skipping auto-table creation: {e}")
        # Safe self-healing SQLite column alteration
        try:
            db.session.execute(db.text("ALTER TABLE system_setting ADD COLUMN default_layout VARCHAR(50) DEFAULT 'sidebar';"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        # Safe self-healing for login_banner_path
        try:
            db.session.execute(db.text("ALTER TABLE system_setting ADD login_banner_path VARCHAR(255) DEFAULT 'img/login_hero.png';"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Safe self-healing for SMTP columns
        for col, col_type in [
            ('smtp_server', 'VARCHAR(255) NULL'),
            ('smtp_port', 'INTEGER DEFAULT 587'),
            ('smtp_user', 'VARCHAR(255) NULL'),
            ('smtp_password', 'VARCHAR(255) NULL'),
            ('receiver_email', 'VARCHAR(255) NULL'),
            ('typography', "VARCHAR(100) DEFAULT 'Inter'")
        ]:
            try:
                db.session.execute(db.text(f"ALTER TABLE system_setting ADD {col} {col_type};"))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # Safe self-healing for user columns
        for col, col_type in [
            ('email_verified', 'BOOLEAN DEFAULT 0'),
            ('email_token_expiry', 'DATETIME NULL'),
            ('password_reset_token', 'VARCHAR(256) NULL'),
            ('password_reset_token_expiry', 'DATETIME NULL'),
            ('deactivation_reason', 'VARCHAR(1000) NULL'),
            ('rejection_reason', 'VARCHAR(1000) NULL')
        ]:
            try:
                db.session.execute(db.text(f"ALTER TABLE user ADD {col} {col_type};"))
                db.session.commit()
            except Exception:
                db.session.rollback()

        from app.models.models import SystemSetting
        try:
            s = SystemSetting.query.first()
            if not s:
                db.session.add(SystemSetting(theme_color='blue', logo_path='img/logo.png', default_layout='sidebar', typography='Inter'))
                db.session.commit()
            elif not s.typography:
                s.typography = 'Inter'
                db.session.commit()
        except Exception:
            db.session.rollback()

    @app.context_processor
    def inject_system_settings():
        from app.models.models import SystemSetting
        from flask import url_for
        try:
            settings = SystemSetting.query.first()
            theme = settings.theme_color if settings else 'blue'
            logo = settings.logo_path if settings else 'img/logo.png'
            banner = settings.login_banner_path if settings and hasattr(settings, 'login_banner_path') else 'img/login_hero.png'
            layout = settings.default_layout if settings and settings.default_layout else 'sidebar'
            typography = settings.typography if settings and hasattr(settings, 'typography') and settings.typography else 'Inter'
        except Exception:
            theme = 'blue'
            logo = 'img/logo.png'
            banner = 'img/login_hero.png'
            layout = 'sidebar'
            typography = 'Inter'
        logo_url = url_for('static', filename=logo)
        banner_url = url_for('static', filename=banner) if banner else url_for('static', filename='img/login_hero.png')
        return {
            'system_theme': theme,
            'system_logo_url': logo_url,
            'system_banner_url': banner_url,
            'system_layout': layout,
            'system_typography': typography
        }

    from app.routes.auth import auth
    from app.routes.admin import admin
    from app.routes.customer import customer
    from app.routes.tracking import tracking_bp
    from app.routes.edi import edi
    from app.routes.notices import notices
    from app.routes.billing import billing
    from app.routes.agent import agent_bp
    from app.routes.soa import soa_bp
    from app.routes.ap_invoices import ap_invoices_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(customer, url_prefix='/customer')
    app.register_blueprint(tracking_bp, url_prefix='/tracking')
    app.register_blueprint(edi, url_prefix='/edi')
    app.register_blueprint(notices, url_prefix='/notices')
    app.register_blueprint(billing, url_prefix='/billing')
    app.register_blueprint(agent_bp, url_prefix='/agent')
    app.register_blueprint(soa_bp, url_prefix='/soa')
    app.register_blueprint(ap_invoices_bp, url_prefix='/ap-invoices')
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        from app.models import models
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Skipping second auto-table creation: {e}")
        try:
            seed_admin()
            seed_lookups()
        except Exception as e:
            print(f"Seeding skipped or failed: {e}")
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'agent':
                return redirect(url_for('agent.dashboard'))
            return redirect(url_for('customer.dashboard'))
        return redirect(url_for('auth.login'))

    # Legacy Redirects to prevent 404s after blueprint prefixing
    @app.route('/login')
    def legacy_login(): return redirect(url_for('auth.login'))
    
    @app.route('/register')
    def legacy_register(): return redirect(url_for('auth.register'))
    
    @app.route('/dashboard')
    def legacy_dashboard():
        if current_user.is_authenticated:
            if current_user.role == 'admin': return redirect(url_for('admin.dashboard'))
            if current_user.role == 'agent': return redirect(url_for('agent.dashboard'))
            return redirect(url_for('customer.dashboard'))
        return redirect(url_for('auth.login'))

    @app.context_processor
    def inject_company_details():
        return dict(company=app.config.get('COMPANY_DETAILS'))

    # Prevent browser from caching authenticated pages.
    # After logout, pressing Back will NOT show the old page.
    @app.after_request
    def no_cache_for_auth_pages(response):
        from flask_login import current_user
        if current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    return app

def seed_admin():
    from app.models.models import User
    from werkzeug.security import generate_password_hash

    admin_user = User.query.filter_by(email='admin@axeglobal.com').first()
    if not admin_user:
        admin_user = User(
            name='System Admin',
            email='admin@axeglobal.com',
            password_hash=generate_password_hash('Admin@123456!'),
            role='admin',
            status='active'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: admin@axeglobal.com / Admin@123456!")

    demo_customer = User.query.filter_by(email='customer@demo.com').first()
    if not demo_customer:
        demo_customer = User(
            name='Demo Customer',
            email='customer@demo.com',
            password_hash=generate_password_hash('Customer@123456!'),
            role='customer',
            status='active'
        )
        db.session.add(demo_customer)
        db.session.commit()
        print("Demo customer created: customer@demo.com / Customer@123456!")


def seed_lookups():
    from app.models.models import Lookup
    
    # Check if empty
    try:
        if Lookup.query.first():
            return
    except Exception as e:
        print("Lookup table check failed, will try after tables created:", e)
        return
        
    initial_lookups = [
        # Currency
        ('currency', 'USD', 'US Dollar', None),
        ('currency', 'EUR', 'Euro', None),
        ('currency', 'GBP', 'British Pound', None),
        ('currency', 'AED', 'UAE Dirham', None),
        ('currency', 'INR', 'Indian Rupee', None),
        ('currency', 'CNY', 'Chinese Yuan', None),
        ('currency', 'SGD', 'Singapore Dollar', None),
        ('currency', 'JPY', 'Japanese Yen', None),
        
        # Weight UOM
        ('weight_uom', 'KG', 'Kilograms', None),
        ('weight_uom', 'LB', 'Pounds', None),
        ('weight_uom', 'MT', 'Metric Ton', None),
        ('weight_uom', 'TON', 'Short Ton', None),
        
        # Volume UOM
        ('volume_uom', 'CBM', 'Cubic Metre', None),
        ('volume_uom', 'CFT', 'Cubic Feet', None),
        ('volume_uom', 'LTR', 'Litres', None),
        
        # Freight Terms
        ('freight_terms', 'prepaid', 'Prepaid', None),
        ('freight_terms', 'collect', 'Collect', None),
        ('freight_terms', 'third_party', 'Third Party', None),
        
        # Incoterms
        ('incoterm', 'FCA', 'FCA - Free Carrier', None),
        ('incoterm', 'FOB', 'FOB - Free On Board', None),
        ('incoterm', 'CFR', 'CFR - Cost and Freight', None),
        ('incoterm', 'CIF', 'CIF - Cost, Insurance & Freight', None),
        ('incoterm', 'DAP', 'DAP - Delivered At Place', None),
        ('incoterm', 'DDP', 'DDP - Delivered Duty Paid', None),
        ('incoterm', 'DPU', 'DPU - Delivered at Place Unloaded', None),
        ('incoterm', 'EXW', 'EXW - Ex Works', None),
        
        # Package Types
        ('package_type', 'pallets', 'Pallets', None),
        ('package_type', 'boxes', 'Boxes/Crates', None),
        ('package_type', 'drums', 'Drums', None),
        ('package_type', 'bags', 'Bags', None),
        ('package_type', 'other', 'Other', None),
        
        # Container Types
        ('container_type', '20ST', '20\' Standard', None),
        ('container_type', '40ST', '40\' Standard', None),
        ('container_type', '40HC', '40\' High Cube', None),
        ('container_type', '20RF', '20\' Reefer', None),
        ('container_type', '40RF', '40\' Reefer', None),
        
        # Carriers
        ('carrier', 'MAERSK', 'MAERSK', None),
        ('carrier', 'MSC', 'MSC', None),
        ('carrier', 'CMA_CGM', 'CMA CGM', None),
        ('carrier', 'COSCO', 'COSCO', None),
        ('carrier', 'ONE', 'Ocean Network Express', None),
        ('carrier', 'HAPAG', 'Hapag-Lloyd', None),
        
        # NVOCCs
        ('nvocc', 'OceanLink', 'OceanLink Express', None),
        ('nvocc', 'GlobalFreight', 'GlobalFreight Line', None),
        ('nvocc', 'FastTransit', 'FastTransit Cargo', None),
    ]
    
    for category, code, name, extra_info in initial_lookups:
        db.session.add(Lookup(category=category, code=code, name=name, extra_info=extra_info))
        
    db.session.commit()
    print("Database lookups successfully seeded.")


# ====================================================================
# AZURE & GUNICORN NAMESPACE COLLISION HOTFIX
# ====================================================================
# When Azure Gunicorn executes 'app:app', standard Python import rules
# prioritize the 'app' package folder over the 'app.py' file. 
#
# To guarantee an instant, self-healing boot without requiring manual 
# Azure Portal config changes, we instantiate and expose the Flask 
# factory 'app' directly at the package root ONLY when running in Azure.
# ====================================================================
if 'WEBSITE_INSTANCE_ID' in os.environ:
    app = create_app()
