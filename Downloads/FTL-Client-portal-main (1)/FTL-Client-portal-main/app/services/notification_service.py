import os
from flask import render_template
import sys
import bidi
# Monkey-patch python-bidi 0.4.2 so it exposes get_display at the root namespace, 
# required by xhtml2pdf without needing a Rust compiler to install newer python-bidi versions.
if not hasattr(bidi, 'get_display'):
    from bidi import algorithm
    bidi.get_display = algorithm.get_display
    sys.modules['bidi'] = bidi

from xhtml2pdf import pisa
from app.models.models import ArrivalNotice, Booking
from app import db
from datetime import datetime
import io

class NotificationService:
    @staticmethod
    def generate_arrival_notice_pdf(booking, recipient_data):
        """
        Generates a personalized PDF for a recipient.
        """
        # Mock charges for demo
        charges = [
            {'name': 'Destination D/O Fee', 'rate': 85.00, 'unit': 'Per HBL', 'total': 85.00},
            {'name': 'THC (Terminal Handling)', 'rate': 35.00, 'unit': 'Per CBM', 'total': 35.00 * (booking.volume or 1)},
            {'name': 'Warehouse Unstuffing', 'rate': 25.00, 'unit': 'Per CBM', 'total': 25.00 * (booking.volume or 1)},
        ]
        total_charges = sum(c['total'] for c in charges)

        html_content = render_template('docs/arrival_notice.html', 
                                     booking=booking, 
                                     recipient_name=recipient_data['name'],
                                     recipient_type=recipient_data['type'],
                                     recipient_email=recipient_data['email'],
                                     charges=charges,
                                     total_charges=total_charges)
        
        pdf_dir = os.path.join('uploads', 'arrival_notices')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        filename = f"AN_{booking.id}_{recipient_data['type']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)
        
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        return pdf_path if not pisa_status.err else None

    @staticmethod
    def notify_all_parties(booking_id):
        booking = Booking.query.get(booking_id)
        if not booking: return {"success": False, "message": "Booking not found"}

        # Fetch details from linked EDI if available
        from app.models.models import EdiPreAlert
        edi = EdiPreAlert.query.filter_by(booking_id=booking.id).first()
        
        mbl = getattr(booking, 'mbl_number', None) or (edi.mbl_number if edi else 'TBA')
        hbl = getattr(booking, 'hbl_number', None) or (edi.hbl_number if edi else 'TBA')

        # Define recipients based on the shipment context
        recipients = [
            {'name': booking.customer.name if booking.customer else 'Valued Buyer', 'type': 'Buyer', 'email': booking.customer.email if booking.customer else 'buyer@example.com'},
            {'name': 'Euro Broker GmbH', 'type': 'Customs Broker', 'email': 'broker@example.com'},
            {'name': 'Hamburg Port Logistics', 'type': 'Destination Agent', 'email': 'agent@hamburg.com'},
            {'name': 'Schnell Trucking', 'type': 'Trucker', 'email': 'trucks@example.com'}
        ]

        success_count = 0
        for rec in recipients:
            pdf_path = NotificationService.generate_arrival_notice_pdf(booking, rec)
            if pdf_path:
                notice = ArrivalNotice(
                    booking_id=booking.id,
                    recipient_type=rec['type'],
                    recipient_email=rec['email'],
                    status='sent',
                    sent_at=datetime.utcnow(),
                    pdf_path=pdf_path
                )
                db.session.add(notice)
                success_count += 1
        
    @staticmethod
    def generate_invoice_pdf(invoice):
        """
        Generates a professional tax invoice PDF.
        """
        html_content = render_template('docs/invoice_pdf.html', invoice=invoice)
        
        pdf_dir = os.path.join('uploads', 'invoices')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        filename = f"INV_{invoice.invoice_number.replace('/', '_')}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)
        
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        if not pisa_status.err:
            invoice.pdf_path = pdf_path
            db.session.commit()
            return pdf_path
        return None

    @staticmethod
    def generate_proforma_pdf(proforma):
        """
        Generates a professional proforma invoice PDF.
        """
        html_content = render_template('docs/proforma_pdf.html', proforma=proforma)
        
        pdf_dir = os.path.join('uploads', 'proformas')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        filename = f"PROFORMA_{proforma.id}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)
        
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        return pdf_path if not pisa_status.err else None

    @staticmethod
    def generate_delivery_order_pdf(booking):
        """
        Generates a professional delivery order (DO) PDF.
        """
        html_content = render_template('docs/delivery_order.html', 
                                     booking=booking, 
                                     datetime=datetime)
        
        pdf_dir = os.path.join('uploads', 'delivery_orders')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        filename = f"DO_{booking.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)
        
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        return pdf_path if not pisa_status.err else None
