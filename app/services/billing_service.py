from datetime import datetime, timedelta
from app.models.models import ProformaInvoice, Invoice, TrackingEvent, Booking
from app import db
import uuid

class BillingService:
    @staticmethod
    def create_proforma(booking):
        """
        Generates a Proforma Invoice based on the booking's rate data.
        """
        try:
            # Check if proforma already exists
            if booking.proforma:
                return {"success": False, "message": "Proforma already exists"}

            # Build charge lines (simplified for demo)
            # In real case, we'd pull these from the Rate engine or specific surcharges
            charge_lines = [
                {"description": "Ocean Freight (LCL)", "amount": booking.total_cost * 0.8, "currency": "EUR"},
                {"description": "Destination THC", "amount": 120.00, "currency": "EUR"},
                {"description": "Documentation Fee", "amount": 45.00, "currency": "EUR"},
                {"description": "Agency Fee", "amount": 95.00, "currency": "EUR"}
            ]
            
            subtotal = sum(c['amount'] for c in charge_lines)
            taxes = subtotal * 0.0; # No tax for international freight usually, or 0%
            total = subtotal + taxes

            proforma = ProformaInvoice(
                booking_id=booking.id,
                charge_lines=charge_lines,
                subtotal=subtotal,
                taxes=taxes,
                total_amount=total,
                currency='EUR',
                valid_until=datetime.utcnow() + timedelta(days=14),
                payment_status='UNPAID'
            )
            
            db.session.add(proforma)
            
            # Add tracking event
            event = TrackingEvent(
                booking_id=booking.id,
                status="Proforma Invoice Issued",
                location="Billing Dept",
                timestamp=datetime.utcnow()
            )
            db.session.add(event)
            
            db.session.commit()
            return {"success": True, "proforma_id": proforma.id}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    @staticmethod
    def confirm_payment(proforma, payment_ref, admin_user_id):
        """
        Confirms payment, updates status, triggers final invoice, and releases documentation.
        """
        from app.models.models import AuditLog
        try:
            now = datetime.utcnow()
            proforma.payment_status = 'CONFIRMED'
            proforma.payment_reference = payment_ref
            proforma.payment_confirmed_at = now
            proforma.confirmed_by_id = admin_user_id
            
            # Update booking status
            booking = proforma.booking
            booking.payment_status = 'CONFIRMED'
            booking.status = 'Documentation Released'
            
            # Create Final Invoice
            invoice_number = f"AXEGLOBAL/{now.year}/{str(proforma.id).zfill(4)}"
            final_invoice = Invoice(
                proforma_id=proforma.id,
                booking_id=booking.id,
                invoice_number=invoice_number,
                charge_lines=proforma.charge_lines,
                total_amount=proforma.total_amount,
                currency=proforma.currency,
                is_tax_invoice=True,
                issued_at=now
            )
            db.session.add(final_invoice)
            
            # Create Audit Log
            audit = AuditLog(
                user_id=admin_user_id,
                action="Payment Confirmed & Cargo Released",
                target_type="Booking",
                target_id=booking.id,
                details=f"Payment ref: {payment_ref}. Released Final Invoice {invoice_number}.",
                timestamp=now
            )
            db.session.add(audit)
            
            # Add tracking event
            event = TrackingEvent(
                booking_id=booking.id,
                status="CARGO RELEASED - Delivery Order Issued",
                location="Billing Dept",
                timestamp=now
            )
            db.session.add(event)
            
            db.session.commit()
            return {"success": True, "invoice_number": invoice_number}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    @staticmethod
    def is_released(booking):
        """
        Programmatic check for the Hard Payment Gate.
        """
        return booking.payment_status == 'CONFIRMED'
