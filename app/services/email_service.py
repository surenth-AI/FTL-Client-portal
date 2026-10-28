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
    def send_email(to_email, subject, html_content, attachment_data=None, attachment_filename=None, user=None, cc=None, bcc=None):
        import re
        from app.models.models import User
        from app.services.customer_settings import effective_settings
        if user is None:
            user = User.query.filter_by(email=to_email).first()
        settings = effective_settings(user)
        if not settings or not settings.smtp_server or not settings.smtp_user or not settings.smtp_password:
            print("SystemMailer Error: SMTP settings are incomplete in the Admin Dashboard.")
            return False

        def parse_addrs(val):
            if not val:
                return []
            if isinstance(val, list):
                return [str(v).strip() for v in val if v and str(v).strip()]
            return [v.strip() for v in re.split(r'[,;]+', str(val)) if v.strip()]

        to_list = parse_addrs(to_email)
        cc_list = parse_addrs(cc)
        bcc_list = parse_addrs(bcc)

        if not to_list:
            print("SystemMailer Error: No recipient email specified.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        sender_name = getattr(settings, 'smtp_sender_name', None) or getattr(settings, 'company_name', None) or 'Admin'
        msg['From'] = f"{sender_name} <{settings.smtp_user}>"
        msg['To'] = ", ".join(to_list)
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)

        msg.attach(MIMEText(html_content, 'html'))
        
        if attachment_data and attachment_filename:
            from email.mime.application import MIMEApplication
            part = MIMEApplication(attachment_data, Name=attachment_filename)
            part['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
            msg.attach(part)

        all_recipients = list(dict.fromkeys(to_list + cc_list + bcc_list))

        try:
            server = smtplib.SMTP(settings.smtp_server, int(settings.smtp_port or 587))
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, all_recipients, msg.as_string())
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

    @staticmethod
    def send_account_activated(user_name, user_email, login_url, erp_customer_code=None):
        """
        Sent to the customer when Atlas ERP activates their portal account.
        """
        code_line = f"<li><strong>Your Customer Code:</strong> {erp_customer_code}</li>" if erp_customer_code else ""
        subject = "Your FTL Portal Account is Now Active"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 30px; color: #1a1a2e; background: #f9fafb; border-radius: 10px;">
            <div style="text-align:center; margin-bottom: 24px;">
                <h1 style="color: #0d47a1; font-size: 1.6rem; margin-bottom: 4px;">Account Activated ✅</h1>
                <p style="color: #555; font-size: 0.95rem;">Fast Transit Line – Client Portal</p>
            </div>
            <p style="font-size: 1rem;">Hi <strong>{user_name}</strong>,</p>
            <p style="font-size: 0.95rem; line-height: 1.6;">
                Great news! Your account on the <strong>FTL Client Portal</strong> has been reviewed and 
                <span style="color: #059669; font-weight: 600;">activated</span>. You can now log in and 
                start managing your shipments, quotes, and bookings.
            </p>
            <ul style="font-size: 0.95rem; line-height: 2;">
                <li><strong>Email:</strong> {user_email}</li>
                {code_line}
            </ul>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_url}" 
                   style="display:inline-block; padding: 12px 30px; background-color: #0d47a1; 
                          color: #fff; text-decoration: none; border-radius: 6px; font-size: 1rem; font-weight: 600;">
                    Log In to Portal →
                </a>
            </div>
            <p style="font-size: 0.85rem; color: #888;">
                If you have any questions, please contact our team. Do not reply to this email directly.
            </p>
        </div>
        """
        return SystemMailer.send_email(user_email, subject, html)

    @staticmethod
    def get_branch_office_emails(branch_id, transaction_type, user=None):
        """
        Retrieves the configured office notification email address(es) for a specific branch and transaction type ('quote' or 'booking').
        Supports one or multiple semicolon-separated emails. Falls back to 'default' branch or receiver_email.
        """
        import json
        from app.services.customer_settings import effective_settings
        settings = effective_settings(user)
        branch_notifs = getattr(settings, 'branch_notifications', None) or {}
        if isinstance(branch_notifs, str):
            try:
                branch_notifs = json.loads(branch_notifs)
            except Exception:
                branch_notifs = {}

        b_key = str(branch_id or '').strip()
        field_key = f"{transaction_type.lower()}_emails"

        if b_key and b_key in branch_notifs:
            emails = (branch_notifs[b_key].get(field_key) or '').strip()
            if emails:
                return emails

        return None

    @staticmethod
    def send_online_quote_notification(quote_id, user_id=None):
        """
        Automatically emails quotation transaction to the customer, and CCs the configured branch office(s).
        """
        from app.models.models import Booking, User
        from app.services.customer_settings import effective_settings
        from app.routes.customer import get_booking_safely, download_pdf

        ref = str(quote_id).strip()
        quote = get_booking_safely(ref, user_id=user_id) if user_id else None
        if not quote:
            quote = get_booking_safely(ref)
        if not quote:
            quote = Booking.query.filter_by(api_booking_ref=ref).first()
        if not quote:
            print(f"send_online_quote_notification: Quote {quote_id} not found.")
            return False

        user = User.query.get(user_id) if user_id else getattr(quote, 'user', None)
        customer_email = (user.email if user else (quote.user.email if quote.user else '')).strip()

        branch_id = '1'
        if user and getattr(user, 'branches', None):
            try:
                branch_id = str(user.branches[0].branch_id)
            except Exception:
                pass

        office_emails = SystemMailer.get_branch_office_emails(branch_id, 'quote', user=user)

        if not customer_email and not office_emails:
            print(f"send_online_quote_notification: Neither customer nor branch office email found for quote {quote_id}.")
            return False

        settings = effective_settings(user)
        co_name = getattr(settings, 'company_name', None) or 'Fast Transit Line'

        # Generate PDF attachment
        pdf_data = None
        try:
            resp = download_pdf(quote_id=quote_id)
            if hasattr(resp, 'get_data') and resp.status_code == 200:
                pdf_data = resp.get_data()
        except Exception as e:
            print(f"send_online_quote_notification: Error generating PDF: {e}")

        origin_val = getattr(quote, 'origin', '') or 'N/A'
        dest_val = getattr(quote, 'destination', '') or 'N/A'
        carrier_val = getattr(quote, 'selected_nvocc', '') or 'Standard'
        service_val = getattr(quote, 'service_type', '') or 'LCL'
        vol_val = getattr(quote, 'volume', 0) or 0
        cost_val = getattr(quote, 'total_cost', 0) or 0.0
        cust_name = getattr(user, 'name', None) or 'Valued Customer'
        company_val = getattr(user, 'company_name', None) or getattr(user, 'name', '')

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 620px; margin: auto; padding: 28px; color: #1e293b; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;">
            <div style="border-bottom: 2px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px;">
                <h2 style="color: #1e3a8a; margin: 0; font-size: 1.45rem;">New Online Quotation: {quote_id}</h2>
                <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">{co_name} · Client Portal Confirmation</div>
            </div>
            
            <p style="font-size: 1rem; margin-bottom: 12px;">Hello <strong>{cust_name}</strong>,</p>
            
            <p style="font-size: 0.95rem; line-height: 1.6; color: #334155; margin-bottom: 16px;">
                Thank you for using the <strong>{co_name}</strong> client portal. Your online quotation reference <strong>{quote_id}</strong> has been generated successfully. A copy of the quotation document is attached as a PDF.
            </p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9rem; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569; width: 35%;">Routing:</td>
                    <td style="padding: 10px 14px; color: #0f172a; font-weight: 600;">{origin_val} &rarr; {dest_val}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Carrier / NVOCC:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{carrier_val}</td>
                </tr>
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Service Type:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{service_val}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Total Volume:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{vol_val} CBM</td>
                </tr>
                <tr style="background-color: #eff6ff;">
                    <td style="padding: 12px 14px; font-weight: bold; color: #1e40af;">Total Amount:</td>
                    <td style="padding: 12px 14px; color: #1e3a8a; font-size: 1.15rem; font-weight: 800;">${cost_val:,.2f}</td>
                </tr>
            </table>

            <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 12px 16px; margin: 20px 0; font-size: 0.88rem; color: #475569;">
                📎 <strong>Attachment:</strong> Quotation_{quote_id}.pdf (Official Quotation Document)
            </div>

            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 12px 16px; margin-top: 20px; font-size: 0.85rem; color: #475569;">
                <strong>Customer Details:</strong> {cust_name} ({customer_email}) · {company_val}<br>
                <strong>Origin Branch ID:</strong> {branch_id}
            </div>

            <div style="margin-top: 28px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 0.85rem; color: #64748b;">
                <strong>{co_name}</strong> · Customer Care &amp; Operations
            </div>
        </div>
        """

        subject = f"Quotation Confirmation - {quote_id} | {origin_val} to {dest_val}"

        if customer_email:
            to_email = customer_email
            cc_email = office_emails
        else:
            to_email = office_emails
            cc_email = None

        return SystemMailer.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html,
            attachment_data=pdf_data,
            attachment_filename=f"Quotation_{quote_id}.pdf",
            user=user,
            cc=cc_email
        )

    @staticmethod
    def send_online_booking_notification(booking_id, user_id=None):
        """
        Automatically emails booking confirmation to the customer, and CCs the configured branch office(s).
        """
        from app.models.models import Booking, User
        from app.services.customer_settings import effective_settings

        booking = Booking.query.get(int(booking_id))
        if not booking:
            print(f"send_online_booking_notification: Booking {booking_id} not found.")
            return False

        user = User.query.get(user_id) if user_id else getattr(booking, 'user', None)
        customer_email = (user.email if user else (booking.user.email if booking.user else '')).strip()

        branch_id = '1'
        if user and getattr(user, 'branches', None):
            try:
                branch_id = str(user.branches[0].branch_id)
            except Exception:
                pass

        office_emails = SystemMailer.get_branch_office_emails(branch_id, 'booking', user=user)

        if not customer_email and not office_emails:
            print(f"send_online_booking_notification: Neither customer nor branch office email found for booking {booking_id}.")
            return False

        settings = effective_settings(user)
        co_name = getattr(settings, 'company_name', None) or 'Fast Transit Line'

        origin_val = booking.origin or 'N/A'
        dest_val = booking.destination or 'N/A'
        por_val = booking.place_of_receipt or origin_val
        del_val = booking.place_of_delivery or dest_val
        service_val = booking.service_type or 'LCL'
        vol_val = booking.volume or 0.0
        cust_ref = booking.customer_ref or 'N/A'
        freight_terms = booking.freight_terms or 'Prepaid'
        cust_name = getattr(user, 'name', None) or 'Valued Customer'
        company_val = getattr(user, 'company_name', None) or getattr(user, 'name', '')
        booking_ref_display = f"BK-{booking.id:06d}"

        # Cargo items summary
        items_summary = ""
        if booking.cargo_items:
            items_summary = f"<div style='margin-top:10px; font-size:0.88rem; color:#475569;'><strong>Cargo:</strong> {len(booking.cargo_items)} item(s) declared</div>"

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 620px; margin: auto; padding: 28px; color: #1e293b; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;">
            <div style="border-bottom: 2px solid #059669; padding-bottom: 16px; margin-bottom: 24px;">
                <h2 style="color: #065f46; margin: 0; font-size: 1.45rem;">Booking Confirmed: {booking_ref_display} ✅</h2>
                <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">{co_name} · Online Booking Request</div>
            </div>
            
            <p style="font-size: 1rem; margin-bottom: 12px;">Hello <strong>{cust_name}</strong>,</p>
            
            <p style="font-size: 0.95rem; line-height: 1.6; color: #334155; margin-bottom: 16px;">
                Thank you! Your online booking request has been submitted successfully to <strong>{co_name}</strong>. Our operations team is reviewing the details and will contact you with shipping documentation.
            </p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9rem; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569; width: 35%;">Booking Reference:</td>
                    <td style="padding: 10px 14px; color: #0f172a; font-weight: 700;">{booking_ref_display}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Customer Reference:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{cust_ref}</td>
                </tr>
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Routing:</td>
                    <td style="padding: 10px 14px; color: #0f172a; font-weight: 600;">{origin_val} &rarr; {dest_val}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Receipt / Delivery:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{por_val} / {del_val}</td>
                </tr>
                <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Service &amp; Volume:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{service_val} · {vol_val} CBM</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #475569;">Freight Terms:</td>
                    <td style="padding: 10px 14px; color: #0f172a;">{freight_terms}</td>
                </tr>
            </table>

            {items_summary}

            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 12px 16px; margin-top: 20px; font-size: 0.85rem; color: #475569;">
                <strong>Customer Details:</strong> {cust_name} ({customer_email}) · {company_val}<br>
                <strong>Handling Branch ID:</strong> {branch_id}
            </div>

            <div style="margin-top: 28px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 0.85rem; color: #64748b;">
                <strong>{co_name}</strong> · Customer Operations &amp; Bookings
            </div>
        </div>
        """

        subject = f"Booking Confirmation - {booking_ref_display} | {origin_val} to {dest_val}"

        if customer_email:
            to_email = customer_email
            cc_email = office_emails
        else:
            to_email = office_emails
            cc_email = None

        return SystemMailer.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html,
            user=user,
            cc=cc_email
        )


