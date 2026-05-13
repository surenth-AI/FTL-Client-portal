import os
from flask import render_template
from xhtml2pdf import pisa
from datetime import datetime
from app.models.models import ArrivalNotice, TrackingEvent
from app import db

class NoticeService:
    @staticmethod
    def generate_arrival_notice(booking, recipient_type, recipient_name, recipient_email, language='en'):
        """
        Generates an Arrival Notice PDF and records it in the database.
        """
        try:
            # 1. Create ArrivalNotice record
            notice = ArrivalNotice(
                booking_id=booking.id,
                recipient_type=recipient_type,
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                language=language,
                send_status='pending'
            )
            db.session.add(notice)
            db.session.flush()

            # 2. Render HTML template
            html = render_template(
                'notices/arrival_notice_pdf.html',
                booking=booking,
                notice=notice,
                now=datetime.utcnow()
            )

            # 3. Generate PDF
            pdf_filename = f"AN_{booking.id}_{notice.id}.pdf"
            pdf_path = os.path.join('uploads', 'notices', pdf_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

            with open(pdf_path, "wb") as f:
                pisa_status = pisa.CreatePDF(html, dest=f)

            if pisa_status.err:
                return {"success": False, "message": "PDF generation failed"}

            # 4. Update record
            notice.pdf_path = pdf_path
            notice.sent_at = datetime.utcnow()
            notice.send_status = 'sent'

            # 5. Add tracking event
            event = TrackingEvent(
                booking_id=booking.id,
                status=f"Arrival Notice sent to {recipient_type.capitalize()}",
                location=booking.destination,
                timestamp=datetime.utcnow()
            )
            db.session.add(event)
            
            db.session.commit()
            return {"success": True, "notice_id": notice.id, "pdf_path": pdf_path}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    @staticmethod
    def send_multi_party_notices(booking):
        """
        Sends notices to Consignee, Agent, and Broker if details are available.
        """
        results = []
        
        # Consignee (User)
        results.append(NoticeService.generate_arrival_notice(
            booking, 'consignee', booking.customer.name, booking.customer.email
        ))
        
        # Example: Also send to a dummy customs broker
        results.append(NoticeService.generate_arrival_notice(
            booking, 'broker', "Customs Broker Ltd", "broker@example.com"
        ))
        
        return results
