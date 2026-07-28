import pandas as pd
from datetime import datetime
from app.models.models import EdiPreAlert, Booking, User, CargoItem
from app import db
import json

class EdiParser:
    @staticmethod
    def parse_payload(payload, source_type='API'):
        """
        Parses a JSON payload and creates an EdiPreAlert record.
        Automatically attempts to create a Booking if data is sufficient.
        """
        try:
            # If payload is a string, parse it
            if isinstance(payload, str):
                data = json.loads(payload)
            else:
                data = payload

            # Extract fields with fallback for AI variations
            mbl = data.get('mbl_number') or data.get('mbl') or data.get('master_bl')
            hbl = data.get('hbl_number') or data.get('hbl') or data.get('house_bl')
            
            if not mbl:
                return {"success": False, "message": f"Missing MBL number. Found: {list(data.keys())}"}
            
            if not hbl:
                # Generate a temporary HBL if missing
                hbl = f"AUTO-HBL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Create EdiPreAlert record
            pre_alert = EdiPreAlert(
                mbl_number=mbl,
                hbl_number=hbl,
                vessel_name=data.get('vessel_name') or data.get('vessel'),
                voyage_number=data.get('voyage_number') or data.get('voyage'),
                port_of_loading=data.get('port_of_loading') or data.get('pol'),
                port_of_discharge=data.get('port_of_discharge') or data.get('pod'),
                eta_pod=datetime.fromisoformat(data.get('eta_pod')) if data.get('eta_pod') else None,
                shipper_name=data.get('shipper_name') or data.get('shipper'),
                consignee_name=data.get('consignee_name') or data.get('consignee'),
                cargo_description=data.get('cargo_description') or data.get('description'),
                weight_kg=float(data.get('weight_kg') or data.get('gross_weight') or data.get('weight') or 0),
                volume_cbm=float(data.get('volume_cbm') or data.get('volume') or 0),
                source_type=source_type,
                raw_payload=data,
                parse_status='parsed'
            )
            
            db.session.add(pre_alert)
            db.session.flush() # Get ID

            # Attempt to auto-create Booking
            items = data.get('items', [])
            booking_result = EdiParser._auto_create_booking(pre_alert, items)
            if booking_result['success']:
                pre_alert.booking_id = booking_result['booking_id']
                db.session.commit()
                return {"success": True, "message": f"EDI Parsed and Booking {booking_result['booking_id']} created", "id": pre_alert.id}
            else:
                pre_alert.parse_status = 'quarantined'
                db.session.commit()
                return {"success": True, "message": f"EDI Parsed but quarantined: {booking_result['message']}", "id": pre_alert.id}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    @staticmethod
    def _auto_create_booking(pre_alert, items=None):
        """
        Logic to create a Booking from an EdiPreAlert.
        Handles multiple cargo items if provided (e.g. from AI extraction).
        """
        try:
            # For demo: Link to the first customer user or admin if none exists
            customer = User.query.filter_by(role='customer').first()
            if not customer:
                customer = User.query.filter_by(role='admin').first()

            if not customer:
                return {"success": False, "message": "No user found to assign booking"}

            # Create the Booking
            new_booking = Booking(
                user_id=customer.id,
                origin=pre_alert.port_of_loading or "Unknown",
                destination=pre_alert.port_of_discharge or "Unknown",
                volume=pre_alert.volume_cbm or 0,
                mbl_number=pre_alert.mbl_number,
                hbl_number=pre_alert.hbl_number,
                vessel_name=pre_alert.vessel_name,
                voyage_number=pre_alert.voyage_number,
                eta_pod=pre_alert.eta_pod,
                selected_nvocc="AI / EDI Ingestion",
                total_cost=0,
                status='Pre-Alert Received',
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_booking)
            db.session.flush()

            # Add Cargo Items
            if items and len(items) > 0:
                for item_data in items:
                    cargo = CargoItem(
                        booking_id=new_booking.id,
                        quantity=int(item_data.get('quantity', 1)),
                        package_type=item_data.get('package_type', 'Package'),
                        weight_kg=float(item_data.get('weight') or item_data.get('weight_kg') or 0),
                        volume_cbm=float(item_data.get('volume') or item_data.get('volume_cbm') or 0),
                        hs_code=item_data.get('hs_code'),
                        description=item_data.get('description') or "Line Item"
                    )
                    db.session.add(cargo)
            else:
                # Default single item
                cargo = CargoItem(
                    booking_id=new_booking.id,
                    weight_kg=pre_alert.weight_kg,
                    volume_cbm=pre_alert.volume_cbm,
                    description=pre_alert.cargo_description or "General Cargo"
                )
                db.session.add(cargo)

            return {"success": True, "booking_id": new_booking.id}
        except Exception as e:
            return {"success": False, "message": f"Auto-booking failed: {str(e)}"}
