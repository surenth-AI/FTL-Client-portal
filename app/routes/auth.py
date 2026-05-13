from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.models import User, Company
from app import db
from app.services.email_service import EmailService
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

auth = Blueprint('auth', __name__)

class CompanyRegistrationForm(FlaskForm):
    # Company Details
    company_name = StringField('Registered Company Name', validators=[DataRequired()])
    address = StringField('Full Address', validators=[DataRequired()])
    zip_code = StringField('Zip Code', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    vat_number = StringField('BTW/VAT Number', validators=[DataRequired()])
    eori_number = StringField('EORI Number', validators=[DataRequired()])
    
    # Contact Person Details
    contact_name = StringField('Contact Person Full Name', validators=[DataRequired()])
    contact_email = StringField('Email ID', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile Number', validators=[DataRequired()])
    
    # Security
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Request Access')

    def validate_vat_number(self, vat_number):
        company = Company.query.filter_by(vat_number=vat_number.data).first()
        if company:
            raise ValidationError('VAT number already exists. Please contact support or use "Join Company".')

    def validate_contact_email(self, contact_email):
        user = User.query.filter_by(email=contact_email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class JoinCompanyForm(FlaskForm):
    ftl_code = StringField('FTL Code', validators=[DataRequired()])
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email ID', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Re-enter Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Request Access')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@auth.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    return render_template('auth/register_selection.html')

@auth.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        # Create Company
        company = Company(
            name=form.company_name.data,
            address=form.address.data,
            zip_code=form.zip_code.data,
            city=form.city.data,
            country=form.country.data,
            vat_number=form.vat_number.data,
            eori_number=form.eori_number.data,
            status='pending_finance'
        )
        db.session.add(company)
        db.session.flush() # Get company.id
        
        # Create User
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.contact_name.data,
            email=form.contact_email.data,
            password_hash=hashed_password,
            role='customer',
            mobile=form.mobile.data,
            company_id=company.id,
            status='pending_ops'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration request submitted! Awaiting Finance and Operations approval.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_company.html', form=form)

@auth.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    form = JoinCompanyForm()
    if form.validate_on_submit():
        company = Company.query.filter_by(ftl_code=form.ftl_code.data).first()
        if not company:
            flash('Invalid FTL Code.', 'danger')
            return render_template('auth/register_user.html', form=form)
        
        # Domain check
        existing_user = User.query.filter_by(company_id=company.id).first()
        if existing_user:
            domain = existing_user.email.split('@')[-1]
            if form.email.data.split('@')[-1] != domain:
                flash(f'Email domain must match the company domain: @{domain}', 'danger')
                return render_template('auth/register_user.html', form=form)
        
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_password,
            role='customer',
            company_id=company.id,
            status='pending_ops'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Join request submitted! Awaiting Operations approval.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_user.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role in ['super_admin', 'admin', 'operation_executive']:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'agent':
            return redirect(url_for('agent.dashboard'))
        return redirect(url_for('customer.dashboard'))
    
    login_form = LoginForm(prefix="login")
    company_form = CompanyRegistrationForm(prefix="company")
    user_form = JoinCompanyForm(prefix="user")
    
    active_tab = 'login' # default state tracker for rendering
    
    # 1. Handle Login Submit
    if login_form.validate_on_submit() and 'login-submit' in request.form:
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and check_password_hash(user.password_hash, login_form.password.data):
            if user.role not in ['super_admin', 'admin']:
                if user.status != 'active':
                    flash(f'Your account is {user.status.replace("_", " ")}. Please wait for approval.', 'warning')
                    return render_template('auth/login.html', form=login_form, company_form=company_form, user_form=user_form, active_tab='login')
                if user.company and user.company.status != 'active':
                    flash(f'Your company status is {user.company.status.replace("_", " ")}. Please wait for approval.', 'warning')
                    return render_template('auth/login.html', form=login_form, company_form=company_form, user_form=user_form, active_tab='login')
            
            login_user(user)
            next_page = request.args.get('next')
            if user.role in ['super_admin', 'admin', 'operation_executive']:
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            elif user.role == 'agent':
                return redirect(next_page) if next_page else redirect(url_for('agent.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('customer.dashboard'))
        else:
            flash('Login unsuccessful. Check email and password.', 'danger')

    # 2. Handle Company Registration Submit
    elif company_form.validate_on_submit() and 'company-submit' in request.form:
        # Create Company
        company = Company(
            name=company_form.company_name.data,
            address=company_form.address.data,
            zip_code=company_form.zip_code.data,
            city=company_form.city.data,
            country=company_form.country.data,
            vat_number=company_form.vat_number.data,
            eori_number=company_form.eori_number.data,
            status='pending_finance'
        )
        db.session.add(company)
        db.session.flush() # Get company.id
        
        # Create User
        hashed_password = generate_password_hash(company_form.password.data)
        user = User(
            name=company_form.contact_name.data,
            email=company_form.contact_email.data,
            password_hash=hashed_password,
            role='customer',
            mobile=company_form.mobile.data,
            company_id=company.id,
            status='pending_ops'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration request submitted! Awaiting Finance and Operations approval.', 'info')
        return redirect(url_for('auth.login'))
    
    elif company_form.errors and 'company-submit' in request.form:
        active_tab = 'reg_company'

    # 3. Handle User Join Submit
    elif user_form.validate_on_submit() and 'user-submit' in request.form:
        company = Company.query.filter_by(ftl_code=user_form.ftl_code.data).first()
        if not company:
            flash('Invalid FTL Code.', 'danger')
            return render_template('auth/login.html', form=login_form, company_form=company_form, user_form=user_form, active_tab='reg_user')
        
        # Domain check
        existing_user = User.query.filter_by(company_id=company.id).first()
        if existing_user:
            domain = existing_user.email.split('@')[-1]
            if user_form.email.data.split('@')[-1] != domain:
                flash(f'Email domain must match the company domain: @{domain}', 'danger')
                return render_template('auth/login.html', form=login_form, company_form=company_form, user_form=user_form, active_tab='reg_user')
        
        hashed_password = generate_password_hash(user_form.password.data)
        user = User(
            name=user_form.name.data,
            email=user_form.email.data,
            password_hash=hashed_password,
            role='customer',
            company_id=company.id,
            status='pending_ops'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Join request submitted! Awaiting Operations approval.', 'info')
        return redirect(url_for('auth.login'))
    
    elif user_form.errors and 'user-submit' in request.form:
        active_tab = 'reg_user'

    # If GET request or failures
    return render_template('auth/login.html', form=login_form, company_form=company_form, user_form=user_form, active_tab=active_tab)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/email/login')
def email_login():
    # Allow login if not authenticated, otherwise just connect Email
    
    flow = EmailService.get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return redirect(authorization_url)

@auth.route('/callback')
def callback():
    flow = EmailService.get_flow()
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    
    # Get user info from Google
    from googleapiclient.discovery import build
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    email = user_info['email']
    name = user_info.get('name', email.split('@')[0])

    # Find or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        # Default new Google users to 'customer' unless they match a specific domain
        role = 'customer'
        if email.endswith('@axeglobal.com'):
             role = 'admin'
             
        user = User(
            name=name,
            email=email,
            password_hash='OAUTH_USER', # Placeholder
            role=role
        )
        db.session.add(user)
        db.session.commit()
        flash(f'New account created for {email}', 'success')
    
    # Save the token to the specific user
    user.email_token = credentials.to_json()
    db.session.commit()
    
    if not credentials.refresh_token:
        flash('Warning: Refresh token not received. Background sync might fail.', 'warning')
    
    login_user(user)
    flash(f'Logged in as {user.name}', 'success')
    
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'agent':
        return redirect(url_for('agent.dashboard'))
    return redirect(url_for('customer.dashboard'))
