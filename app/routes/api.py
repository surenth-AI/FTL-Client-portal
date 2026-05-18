from flask import Blueprint, jsonify, request, redirect, flash, url_for
from werkzeug.security import generate_password_hash
from app import db
from app.models.models import User, UserAccountMapping, UserBranchMapping
from datetime import datetime, timedelta
import secrets

api_bp = Blueprint('api', __name__)

# Shared Secret Token for API Authentication
ATLAS_SHARED_TOKEN = "YOUR_ATLAS_SECRET_TOKEN"

def check_auth(req):
    auth_header = req.headers.get('Authorization')
    return auth_header == f"Bearer {ATLAS_SHARED_TOKEN}"

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

    # In a real setup, redirect to a beautiful UI success page.
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

    # Update Multi-Account Mappings safely
    if 'account_ids' in data:
        UserAccountMapping.query.filter_by(user_id=user.id).delete()
        for acc_id in data['account_ids']:
            db.session.add(UserAccountMapping(user_id=user.id, account_id=acc_id))

    # Update Multi-Branch Mappings safely
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
