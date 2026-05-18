import os
import base64
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.services.edi_parser import EdiParser
from app import db

# Allow HTTP for local development (InsecureTransportError)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = [
    'https://www.googleapis.com/auth/email.readonly',
    'https://www.googleapis.com/auth/email.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
    'openid'
]

class EmailService:
    @staticmethod
    def get_flow():
        return Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=SCOPES,
            redirect_uri='http://localhost:5000/auth/callback'
        )

    @staticmethod
    def get_service(user):
        if not user or not user.email_token:
            return None
        
        try:
            token_data = json.loads(user.email_token)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                user.email_token = creds.to_json()
                db.session.commit()
            
            return build('email', 'v1', credentials=creds)
        except Exception as e:
            print(f"Error loading token for user {user.id}: {e}")
            return None

    @staticmethod
    def sync_edi_emails(user):
        service = EmailService.get_service(user)
        if not service:
            return {"success": False, "message": "Email not authorized for this user"}

        try:
            query = "subject:(EDI OR PRE-ALERT) has:attachment"
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])

            count = 0
            for msg in messages:
                msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
                
                for part in msg_data['payload'].get('parts', []):
                    if part['filename'] and (part['filename'].endswith('.json') or part['filename'].endswith('.csv')):
                        attachment_id = part['body'].get('attachmentId')
                        if attachment_id:
                            attachment = service.users().messages().attachments().get(
                                userId='me', messageId=msg['id'], id=attachment_id).execute()
                            
                            data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                            
                            if part['filename'].endswith('.json'):
                                payload = json.loads(data)
                                result = EdiParser.parse_payload(payload, source_type=f'Email ({user.email})')
                                if result['success']: count += 1

            return {"success": True, "message": f"Synced {count} new EDI shipments from {user.email}"}

        except Exception as e:
            return {"success": False, "message": str(e)}

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.models import SystemSetting

class SystemMailer:
    @staticmethod
    def send_email(to_email, subject, html_content):
        # Fetch settings
        settings = SystemSetting.query.first()
        if not settings or not settings.smtp_server or not settings.smtp_user or not settings.smtp_password:
            print("SystemMailer Error: SMTP settings are incomplete in the Admin Dashboard.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"AxeGlobal Portal <{settings.smtp_user}>"
        msg['To'] = to_email

        msg.attach(MIMEText(html_content, 'html'))

        try:
            server = smtplib.SMTP(settings.smtp_server, int(settings.smtp_port or 587))
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, [to_email], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"SystemMailer Exception: {e}")
            return False

    @staticmethod
    def send_password_reset(user_email, reset_link):
        subject = "AxeGlobal - Password Reset Request"
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2>Password Reset</h2>
            <p>You requested to reset your password. Click the secure link below to proceed:</p>
            <p><a href="{reset_link}" style="display:inline-block; padding: 10px 20px; background-color: #0077ff; color: #fff; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>If you did not request this, please ignore this email.</p>
        </div>
        """
        return SystemMailer.send_email(user_email, subject, html)

    @staticmethod
    def send_approval_request(user_name, user_email, company_name):
        settings = SystemSetting.query.first()
        if not settings or not settings.receiver_email:
            print("SystemMailer Error: Operations Receiver Email not set.")
            return False

        subject = "Action Required: New Portal Registration Request"
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2>New Registration Pending Approval</h2>
            <p>A new user has requested access to the portal:</p>
            <ul>
                <li><strong>Name:</strong> {user_name}</li>
                <li><strong>Email:</strong> {user_email}</li>
                <li><strong>Company:</strong> {company_name}</li>
            </ul>
            <p>Please log in to the admin dashboard to review their request.</p>
        </div>
        """
        return SystemMailer.send_email(settings.receiver_email, subject, html)
