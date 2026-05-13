from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    with app.app_context():
        from app.models import models
        db.create_all()
        # Safe self-healing SQLite column alteration
        try:
            db.session.execute(db.text("ALTER TABLE system_setting ADD COLUMN default_layout VARCHAR(50) DEFAULT 'sidebar';"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        # Safe self-healing for login_banner_path
        try:
            db.session.execute(db.text("ALTER TABLE system_setting ADD COLUMN login_banner_path VARCHAR(255) DEFAULT 'img/login_hero.png';"))
            db.session.commit()
        except Exception:
            db.session.rollback()

        from app.models.models import SystemSetting
        try:
            if not SystemSetting.query.first():
                db.session.add(SystemSetting(theme_color='blue', logo_path='img/logo.png', default_layout='sidebar'))
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
        except Exception:
            theme = 'blue'
            logo = 'img/logo.png'
            banner = 'img/login_hero.png'
            layout = 'sidebar'
        logo_url = url_for('static', filename=logo)
        banner_url = url_for('static', filename=banner) if banner else url_for('static', filename='img/login_hero.png')
        return {
            'system_theme': theme,
            'system_logo_url': logo_url,
            'system_banner_url': banner_url,
            'system_layout': layout
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

    with app.app_context():
        from app.models import models
        db.create_all()
        try:
            seed_admin()
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

    return app

def seed_admin():
    from app.models.models import User
    from werkzeug.security import generate_password_hash
    
    admin_user = User.query.filter_by(email='admin@axeglobal.com').first()
    if not admin_user:
        admin_user = User(
            name='System Admin',
            email='admin@axeglobal.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            status='active'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: admin@axeglobal.com / admin123")


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
