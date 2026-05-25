"""
Registration API routes - uses raw pyodbc to avoid SQLAlchemy HY104 precision
errors with the legacy {SQL Server} ODBC driver when passing NULL parameters.
"""

def _fmt_date(val):
    """Safely convert a date/datetime from pyodbc (may be str or datetime) to ISO string."""
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)
import uuid
import pyodbc
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, abort
from dotenv import load_dotenv

load_dotenv()

api_bp = Blueprint('api', __name__)

# ─────────────────────────────────────────────────────────────
# Raw pyodbc connection helper
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


def _row_to_dict(row, cursor):
    """Convert a pyodbc Row to a plain dict using column descriptions."""
    cols = [col[0] for col in cursor.description]
    return dict(zip(cols, row))


# ─────────────────────────────────────────────────────────────
# POST /api/Registrations  – create a new registration request
# ─────────────────────────────────────────────────────────────
@api_bp.route('/Registrations', methods=['POST'])
def create_registration():
    data = request.get_json() or {}
    required = ['email', 'fullName', 'companyName', 'countryCode']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    reg_id  = str(uuid.uuid4())
    now     = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    email   = data['email']
    name    = data['fullName']
    phone   = data.get('phone') or ''
    company = data['companyName']
    country = data['countryCode']
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
            reg_id, email, name, phone, company, country, vat, now
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'registrationId': reg_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────
# GET /api/Registrations  – list / search with pagination
# ─────────────────────────────────────────────────────────────
@api_bp.route('/Registrations', methods=['GET'])
def list_registrations():
    status    = request.args.get('status', '')
    search    = request.args.get('search', '')
    page      = max(int(request.args.get('page', 1)), 1)
    page_size = max(int(request.args.get('pageSize', 20)), 1)
    offset    = (page - 1) * page_size

    where_clauses = []
    params        = []

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

        # total count
        cursor.execute(f"SELECT COUNT(*) FROM registration {where_sql}", *params)
        total = cursor.fetchone()[0]

        # paginated rows
        cursor.execute(
            f"""
            SELECT id, registration_id, email, full_name, company_name, status, created_on
            FROM registration
            {where_sql}
            ORDER BY created_on DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *params, offset, page_size
        )
        rows = cursor.fetchall()
        items = []
        for r in rows:
            items.append({
                'id':             r[0],
                'registrationId': r[1],
                'email':          r[2],
                'fullName':       r[3],
                'companyName':    r[4],
                'status':         r[5],
                'createdOn':      _fmt_date(r[6]),
            })
        cursor.close()
        conn.close()
        return jsonify({'total': total, 'page': page, 'pageSize': page_size, 'items': items}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────
# GET /api/Registrations/<id>  – get single registration
# ─────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────
# POST /api/Registrations/<id>/approve
# ─────────────────────────────────────────────────────────────
@api_bp.route('/Registrations/<int:reg_id>/approve', methods=['POST'])
def approve_registration(reg_id):
    try:
        conn   = _get_conn()
        cursor = conn.cursor()

        # Fetch registration
        cursor.execute("SELECT id, status, company_name, vat FROM registration WHERE id = ?", reg_id)
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Registration not found'}), 404
        if row[1] != 'pending':
            conn.close()
            return jsonify({'error': 'Registration is not pending'}), 400

        company_name = row[2]
        vat          = row[3] or ''

        # Create Company record
        cursor.execute(
            """
            INSERT INTO company (name, vat_number, status)
            OUTPUT INSERTED.id
            VALUES (?, ?, 'active')
            """,
            company_name, vat
        )
        company_id = cursor.fetchone()[0]

        # Update registration status
        cursor.execute("UPDATE registration SET status = 'approved' WHERE id = ?", reg_id)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Approved', 'companyId': company_id, 'authorized': 1}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────
# POST /api/Registrations/<id>/reject
# ─────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────
# POST /api/Registrations/<id>/request-info
# ─────────────────────────────────────────────────────────────
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
