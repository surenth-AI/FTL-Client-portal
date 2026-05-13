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
