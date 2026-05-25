"""
Unified API Blueprint — contains:
  1. User registration, email verification, password reset (original)
  2. Atlas ERP sync routes (original)
  3. /api/Registrations — tenant registration workflow (new, raw pyodbc)
"""
from flask import Blueprint, jsonify, request, url_for
from werkzeug.security import generate_password_hash
from app import db
from app.models.models import User, UserAccountMapping, UserBranchMapping
from datetime import datetime, timedelta
import secrets
import uuid
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

api_bp = Blueprint('api', __name__)

# ─────────────────────────────────────────────────────────────
# Auth token for Atlas ERP sync
# ─────────────────────────────────────────────────────────────
ATLAS_SHARED_TOKEN = "1"

def check_auth(req):
    auth_header = req.headers.get('Authorization')
    return auth_header == f"Bearer {ATLAS_SHARED_TOKEN}"


# ─────────────────────────────────────────────────────────────
# Raw pyodbc helper (bypasses SQLAlchemy HY104 bug on legacy driver)
# ─────────────────────────────────────────────────────────────
def _get_conn():
    server   = os.environ.get('DB_SERVER')
    database = os.environ.get('DB_NAME')
    username = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    driver   = os.environ.get('DB_DRIVER', '{SQL Server}')
    conn_str = (
        f"Driver={driver};"
        f"Server={server},1433;"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
    )
    return pyodbc.connect(conn_str)


def _fmt_date(val):
    """Safely convert a date/datetime from pyodbc (may be str or datetime) to ISO string."""
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)


# ══════════════════════════════════════════════════════════════
# SECTION 1 — USER REGISTRATION & AUTH (original routes)
# ══════════════════════════════════════════════════════════════

@api_bp.route('/users/register', methods=['POST'])
def api_register():
    """
    Self-registration initiated by users on the Portal.
    ---
    tags:
      - Login and Register API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: John Doe
            email:
              type: string
              example: john.doe@logistics.com
            password:
              type: string
              example: TemporaryPassword123!
    responses:
      201:
        description: Registration successful.
      400:
        description: Email already registered.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({"success": False, "message": "Email already registered."}), 400

    verification_token = secrets.token_urlsafe(32)

    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        status='pending_verification',
        email_token=verification_token,
        email_token_expiry=datetime.utcnow() + timedelta(days=1),
        email_verified=False
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Registration successful. Please verify your email via the link sent.",
        "user_id": new_user.id
    }), 201


@api_bp.route('/users/verify-email', methods=['GET'])
def api_verify_email():
    """
    Email verification link clicked by the user.
    ---
    tags:
      - Login and Register API
    parameters:
      - in: query
        name: token
        type: string
        required: true
        description: Secure email verification token.
    responses:
      200:
        description: Email verified successfully.
      400:
        description: Invalid or expired token.
    """
    token = request.args.get('token')
    if not token:
        return jsonify({"success": False, "message": "Missing token."}), 400

    user = User.query.filter_by(email_token=token).first()
    if not user:
        return jsonify({"success": False, "message": "Invalid token."}), 400

    if user.email_token_expiry and datetime.utcnow() > user.email_token_expiry:
        return jsonify({"success": False, "message": "Token has expired."}), 400

    user.email_verified = True
    user.email_token = None
    user.status = 'pending_approval'
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Your email has been verified! Our operations team is reviewing your details."
    }), 200


@api_bp.route('/users/forgot-password', methods=['POST'])
def api_forgot_password():
    """
    Initiate a password reset via API by generating a secure token.
    ---
    tags:
      - Login and Register API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john.doe@logistics.com
    responses:
      200:
        description: Password reset token generated successfully.
      404:
        description: User not found.
    """
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()

    reset_link = url_for('auth.reset_password', token=token, _external=True)

    return jsonify({
        "success": True,
        "message": "Password reset token generated.",
        "reset_token": token,
        "reset_link": reset_link
    }), 200


@api_bp.route('/users/set-password', methods=['POST'])
def api_set_password():
    """
    Sets or resets a user's password using a time-bound secure token.
    ---
    tags:
      - Login and Register API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            token:
              type: string
              example: secure_activation_or_reset_token
            password:
              type: string
              example: NewSecurePassword456!
    responses:
      200:
        description: Password updated successfully.
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({"success": False, "message": "Missing token or password."}), 400

    user = User.query.filter_by(password_reset_token=token).first()
    if not user:
        return jsonify({"success": False, "message": "Invalid token."}), 400

    if user.password_reset_token_expiry and datetime.utcnow() > user.password_reset_token_expiry:
        return jsonify({"success": False, "message": "Token expired."}), 400

    user.password_hash = generate_password_hash(new_password)
    user.password_reset_token = None
    db.session.commit()

    return jsonify({"success": True, "message": "Password updated successfully. You can now log in."}), 200


# ══════════════════════════════════════════════════════════════
# SECTION 2 — ATLAS ERP SYNC (original routes)
# ══════════════════════════════════════════════════════════════

@api_bp.route('/users/sync', methods=['POST'])
def api_sync():
    """
    Receives status updates, account mapping, and activations from Atlas ERP.
    ---
    tags:
      - ERP Sync API
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john.doe@logistics.com
            status:
              type: string
              example: activated
            account_ids:
              type: array
              items:
                type: string
              example: ["ACT-99210", "ACT-88402"]
            branch_ids:
              type: array
              items:
                type: string
              example: ["DEHAM", "NLROT"]
            rejection_reason:
              type: string
            deactivation_reason:
              type: string
    responses:
      200:
        description: User sync completed successfully.
      401:
        description: Unauthorized.
      404:
        description: User not found.
    """
    if not check_auth(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": f"User {email} not found in Portal."}), 404

    if 'status' in data:
        user.status = data['status']
    if 'rejection_reason' in data:
        user.rejection_reason = data['rejection_reason']
    if 'deactivation_reason' in data:
        user.deactivation_reason = data['deactivation_reason']

    if 'account_ids' in data:
        UserAccountMapping.query.filter_by(user_id=user.id).delete()
        for acc_id in data['account_ids']:
            db.session.add(UserAccountMapping(user_id=user.id, account_id=acc_id))

    if 'branch_ids' in data:
        UserBranchMapping.query.filter_by(user_id=user.id).delete()
        for br_id in data['branch_ids']:
            db.session.add(UserBranchMapping(user_id=user.id, branch_id=br_id))

    db.session.commit()

    return jsonify({"success": True, "message": "User sync completed successfully."}), 200


@api_bp.route('/users/deactivate', methods=['POST'])
def api_deactivate():
    """
    Triggered when a user initiates a deactivation request inside the Portal.
    ---
    tags:
      - ERP Sync API
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: john.doe@logistics.com
            deactivation_reason:
              type: string
              example: Requested by customer from Profile Panel.
    responses:
      200:
        description: Success.
      401:
        description: Unauthorized.
    """
    if not check_auth(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    user.status = 'deactivated'
    user.deactivation_reason = data.get('deactivation_reason', 'Deactivated via API')
    db.session.commit()

    return jsonify({"success": True, "message": "User successfully deactivated."}), 200


# ══════════════════════════════════════════════════════════════
# SECTION 3 — TENANT REGISTRATION WORKFLOW (new, raw pyodbc)
# ══════════════════════════════════════════════════════════════

@api_bp.route('/Registrations', methods=['POST'])
def create_registration():
    data     = request.get_json() or {}
    required = ['email', 'fullName', 'companyName', 'countryCode']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    reg_id  = str(uuid.uuid4())
    now     = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    phone   = data.get('phone') or ''
    vat     = data.get('vat') or ''

    try:
        conn   = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO registration
                (registration_id, email, full_name, phone, company_name,
                 country_code, vat, created_on, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            reg_id, data['email'], data['fullName'], phone,
            data['companyName'], data['countryCode'], vat, now
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'registrationId': reg_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/Registrations', methods=['GET'])
def list_registrations():
    status    = request.args.get('status', '')
    search    = request.args.get('search', '')
    page      = max(int(request.args.get('page', 1)), 1)
    page_size = max(int(request.args.get('pageSize', 20)), 1)
    offset    = (page - 1) * page_size

    where_clauses, params = [], []
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    if search:
        like = f"%{search}%"
        where_clauses.append("(email LIKE ? OR company_name LIKE ? OR full_name LIKE ?)")
        params.extend([like, like, like])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    try:
        conn   = _get_conn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM registration {where_sql}", *params)
        total = cursor.fetchone()[0]

        cursor.execute(
            f"""
            SELECT id, registration_id, email, full_name, company_name, status, created_on
            FROM registration {where_sql}
            ORDER BY created_on DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *params, offset, page_size
        )
        items = [{
            'id':             r[0],
            'registrationId': r[1],
            'email':          r[2],
            'fullName':       r[3],
            'companyName':    r[4],
            'status':         r[5],
            'createdOn':      _fmt_date(r[6]),
        } for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({'total': total, 'page': page, 'pageSize': page_size, 'items': items}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/Registrations/<int:reg_id>', methods=['GET'])
def get_registration(reg_id):
    try:
        conn   = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, registration_id, email, full_name, phone, company_name,
                   country_code, vat, status, created_on, reject_reason, info_message
            FROM registration WHERE id = ?
            """,
            reg_id
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return jsonify({'error': 'Registration not found'}), 404
        return jsonify({
            'id':             row[0],
            'registrationId': row[1],
            'email':          row[2],
            'fullName':       row[3],
            'phone':          row[4],
            'companyName':    row[5],
            'countryCode':    row[6],
            'vat':            row[7],
            'status':         row[8],
            'createdOn':      _fmt_date(row[9]),
            'rejectReason':   row[10],
            'infoMessage':    row[11],
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/Registrations/<int:reg_id>/approve', methods=['POST'])
def approve_registration(reg_id):
    try:
        conn   = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, status, company_name, vat FROM registration WHERE id = ?", reg_id)
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Registration not found'}), 404
        if row[1] != 'pending':
            conn.close()
            return jsonify({'error': 'Registration is not pending'}), 400

        cursor.execute(
            "INSERT INTO company (name, vat_number, status) OUTPUT INSERTED.id VALUES (?, ?, 'active')",
            row[2], row[3] or ''
        )
        company_id = cursor.fetchone()[0]
        cursor.execute("UPDATE registration SET status = 'approved' WHERE id = ?", reg_id)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Approved', 'companyId': company_id, 'authorized': 1}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/Registrations/<int:reg_id>/reject', methods=['POST'])
def reject_registration(reg_id):
    data   = request.get_json() or {}
    reason = data.get('reason', '')
    if not reason:
        return jsonify({'error': 'Reason required'}), 400
    try:
        conn   = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM registration WHERE id = ?", reg_id)
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Registration not found'}), 404
        cursor.execute(
            "UPDATE registration SET status = 'rejected', reject_reason = ? WHERE id = ?",
            reason, reg_id
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Rejected'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/Registrations/<int:reg_id>/request-info', methods=['POST'])
def request_info(reg_id):
    data    = request.get_json() or {}
    message = data.get('message', '')
    if not message:
        return jsonify({'error': 'Message required'}), 400
    try:
        conn   = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM registration WHERE id = ?", reg_id)
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Registration not found'}), 404
        cursor.execute(
            "UPDATE registration SET status = 'info_requested', info_message = ? WHERE id = ?",
            message, reg_id
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Info requested'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
