from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.models import User, Company
from app import db
from app.services.email_service import EmailService, SystemMailer
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.utils import validate_password_strength
from wtforms import SelectField

auth = Blueprint('auth', __name__)


def _password_strength_validator(form, field):
    ok, msg = validate_password_strength(field.data or '')
    if not ok:
        raise ValidationError(msg)


COUNTRIES = [
    ('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AD', 'Andorra'), ('AO', 'Angola'),
    ('AR', 'Argentina'), ('AM', 'Armenia'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'),
    ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'),
    ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BT', 'Bhutan'), ('BO', 'Bolivia'),
    ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BR', 'Brazil'), ('BN', 'Brunei'),
    ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'),
    ('CA', 'Canada'), ('CV', 'Cape Verde'), ('CF', 'Central African Republic'), ('TD', 'Chad'),
    ('CL', 'Chile'), ('CN', 'China'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'),
    ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'),
    ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'),
    ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'),
    ('ET', 'Ethiopia'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GA', 'Gabon'),
    ('GM', 'Gambia'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GR', 'Greece'),
    ('GD', 'Grenada'), ('GT', 'Guatemala'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'),
    ('HT', 'Haiti'), ('HN', 'Honduras'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'),
    ('ID', 'Indonesia'), ('IR', 'Iran'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IL', 'Israel'),
    ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'),
    ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', 'North Korea'), ('KR', 'South Korea'), ('KW', 'Kuwait'),
    ('KG', 'Kyrgyzstan'), ('LA', 'Laos'), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'),
    ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'),
    ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'),
    ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('MX', 'Mexico'),
    ('FM', 'Micronesia'), ('MD', 'Moldova'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'),
    ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'),
    ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'),
    ('NG', 'Nigeria'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'),
    ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'),
    ('PL', 'Poland'), ('PT', 'Portugal'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russia'),
    ('RW', 'Rwanda'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'),
    ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'),
    ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'),
    ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SK', 'Slovakia'),
    ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'),
    ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'),
    ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syria'), ('TW', 'Taiwan'),
    ('TJ', 'Tajikistan'), ('TZ', 'Tanzania'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'),
    ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'),
    ('TM', 'Turkmenistan'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'),
    ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UY', 'Uruguay'),
    ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VA', 'Vatican City'), ('VE', 'Venezuela'),
    ('VN', 'Vietnam'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('XX', 'Other')
]

class JoinCompanyForm(FlaskForm):
    ftl_code = StringField('Company Referral Code', validators=[])
    company_name = StringField('Company Full Name', validators=[DataRequired()])
    city = StringField('Company Location (City)', validators=[DataRequired()])
    country = SelectField('Country', choices=COUNTRIES, validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Corporate Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile/Telephone Number', validators=[])
    password = PasswordField('Password', validators=[DataRequired(), _password_strength_validator])
    confirm_password = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    
    submit = SubmitField('Request Access')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), _password_strength_validator])
    confirm_password = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

@auth.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    return redirect(url_for('auth.login', active_tab='reg_user'))



@auth.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    form = JoinCompanyForm()
    if form.validate_on_submit():
        company_id = None
        if form.ftl_code.data:
            company = Company.query.filter_by(ftl_code=form.ftl_code.data).first()
            if not company:
                flash('Invalid Company Referral Code.', 'danger')
                return render_template('auth/register_user.html', form=form)
            company_id = company.id
            
            # Domain check
            existing_user = User.query.filter_by(company_id=company.id).first()
            if existing_user:
                domain = existing_user.email.split('@')[-1]
                if form.email.data.split('@')[-1] != domain:
                    flash(f'Email domain must match the company domain: @{domain}', 'danger')
                    return render_template('auth/register_user.html', form=form)
        
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=f"{form.first_name.data} {form.last_name.data}",
            email=form.email.data,
            mobile=form.mobile.data,
            password_hash=hashed_password,
            role='customer',
            company_id=company_id,
            status='pending_ops'
        )
        db.session.add(user)
        db.session.commit()
        
        # Post to realnexus system
        import requests
        import uuid
        from datetime import datetime, timezone
        try:
            rn_data = {
                "registrationId": str(uuid.uuid4()),
                "email": form.email.data,
                "fullName": f"{form.first_name.data} {form.last_name.data}",
                "phone": form.mobile.data or "",
                "companyName": company.name if company else form.company_name.data,
                "countryCode": form.country.data,
                "vat": "",
                "createdOn": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
            requests.post('http://realnexus.comit.cloud:5000/api/Registrations', 
                          headers={'accept': '*/*', 'x-api-key': '1', 'Content-Type': 'application/json'},
                          json=rn_data, timeout=10)
        except Exception as e:
            print(f"Error posting to Realnexus: {e}")
        
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
    user_form = JoinCompanyForm(prefix="user")
    
    active_tab = request.args.get('active_tab', 'login') # state tracker for rendering
    
    # 1. Handle Login Submit
    if login_form.validate_on_submit() and 'login-submit' in request.form:
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and check_password_hash(user.password_hash, login_form.password.data):
            if user.role not in ['super_admin', 'admin']:
                if user.status not in ['active', 'activated']:
                    flash(f'Your account is {user.status.replace("_", " ")}. Please wait for approval.', 'warning')
                    return render_template('auth/login.html', form=login_form, user_form=user_form, active_tab='login')
                if user.company and user.company.status != 'active':
                    flash(f'Your company status is {user.company.status.replace("_", " ")}. Please wait for approval.', 'warning')
                    return render_template('auth/login.html', form=login_form, user_form=user_form, active_tab='login')
            
            login_user(user)
            next_page = request.args.get('next')
            if user.role in ['super_admin', 'admin', 'operation_executive']:
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            elif user.role == 'agent':
                return redirect(next_page) if next_page else redirect(url_for('agent.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('customer.dashboard'))
        else:
            flash('Login unsuccessful. Check email and password.', 'danger')

    # 3. Handle User Join Submit
    elif user_form.validate_on_submit() and 'user-submit' in request.form:
        company_id = None
        company = None
        if user_form.ftl_code.data:
            company = Company.query.filter_by(ftl_code=user_form.ftl_code.data).first()
            if not company:
                flash('Invalid Company Referral Code.', 'danger')
                return render_template('auth/login.html', form=login_form, user_form=user_form, active_tab='reg_user')
            company_id = company.id
            
            # Domain check
            existing_user = User.query.filter_by(company_id=company.id).first()
            if existing_user:
                domain = existing_user.email.split('@')[-1]
                if user_form.email.data.split('@')[-1] != domain:
                    flash(f'Email domain must match the company domain: @{domain}', 'danger')
                    return render_template('auth/login.html', form=login_form, user_form=user_form, active_tab='reg_user')
        
        hashed_password = generate_password_hash(user_form.password.data)
        user = User(
            name=f"{user_form.first_name.data} {user_form.last_name.data}",
            email=user_form.email.data,
            mobile=user_form.mobile.data,
            password_hash=hashed_password,
            role='customer',
            company_id=company_id,
            status='pending_ops'
        )
        db.session.add(user)
        db.session.commit()
        
        # Post to realnexus system
        import requests
        import uuid
        from datetime import datetime, timezone
        try:
            rn_data = {
                "registrationId": str(uuid.uuid4()),
                "email": user_form.email.data,
                "fullName": f"{user_form.first_name.data} {user_form.last_name.data}",
                "phone": user_form.mobile.data or "",
                "companyName": company.name if company else user_form.company_name.data,
                "countryCode": user_form.country.data,
                "vat": "",
                "createdOn": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
            requests.post('http://realnexus.comit.cloud:5000/api/Registrations', 
                          headers={'accept': '*/*', 'x-api-key': '1', 'Content-Type': 'application/json'},
                          json=rn_data, timeout=10)
        except Exception as e:
            print(f"Error posting to Realnexus: {e}")
        
        company_display = company.name if company else f"{user_form.company_name.data or 'N/A'} ({user_form.city.data or 'N/A'}, {user_form.country.data or 'N/A'})"
        SystemMailer.send_approval_request(user.name, user.email, company_display)
        
        flash('Join request submitted! Awaiting Operations approval.', 'info')
        return redirect(url_for('auth.login'))
    
    elif user_form.errors and 'user-submit' in request.form:
        active_tab = 'reg_user'

    # If GET request or failures
    return render_template('auth/login.html', form=login_form, user_form=user_form, active_tab=active_tab)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    if current_user.role in ['super_admin', 'admin', 'operation_executive']:
        return render_template('profile/admin.html')
    elif current_user.role == 'agent':
        return render_template('profile/agent.html')
    else:
        return render_template('profile/customer.html')

import secrets
from datetime import datetime, timedelta

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            # Construct reset link
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            mail_sent = SystemMailer.send_password_reset(user.email, reset_link)
            if mail_sent:
                flash('An email has been sent with instructions to reset your password.', 'info')
            else:
                flash(f'SystemMailer failed. Check Admin SMTP config. (Simulated Link: {reset_link})', 'warning')
        else:
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))
    user = User.query.filter_by(password_reset_token=token).first()
    if not user:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('auth.forgot_password'))
        
    if user.password_reset_token_expiry and datetime.utcnow() > user.password_reset_token_expiry:
        flash('That token has expired.', 'warning')
        return redirect(url_for('auth.forgot_password'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password_hash = hashed_password
        user.password_reset_token = None
        user.password_reset_token_expiry = None
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

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
