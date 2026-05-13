from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ftl_code = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    zip_code = db.Column(db.String(20))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    vat_number = db.Column(db.String(50), unique=True)
    eori_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending_finance') # pending_finance, pending_ops, active, rejected
    assigned_ops_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assigned_ops = db.relationship('User', foreign_keys=[assigned_ops_id], backref='assigned_companies')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', foreign_keys='User.company_id', backref='company', lazy=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer') # super_admin, admin, operation_executive, customer
    email_token = db.Column(db.Text, nullable=True) # Stores the JSON serialized token
    mobile = db.Column(db.String(20))
    department = db.Column(db.String(50)) # export, import, warehouse, finance
    status = db.Column(db.String(20), default='pending_ops') # pending_ops, active, rejected
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    bookings = db.relationship('Booking', backref='customer', lazy=True)

class Rate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    nvocc_name = db.Column(db.String(100), nullable=False)
    carrier_name = db.Column(db.String(100), nullable=True)
    frequency = db.Column(db.String(50), nullable=True)
    base_rate = db.Column(db.Float, nullable=False)
    surcharges = db.Column(db.Float, nullable=False)
    transit_days = db.Column(db.Integer, nullable=False)
    validity_start = db.Column(db.Date, nullable=False)
    validity_end = db.Column(db.Date, nullable=False)
    service_type = db.Column(db.String(20), nullable=False, default='LCL') # FCL / LCL
    remarks = db.Column(db.Text, nullable=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    volume = db.Column(db.Float, nullable=False)
    selected_nvocc = db.Column(db.String(100), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    service_type = db.Column(db.String(20), nullable=False, default='LCL') # FCL / LCL
    pickup_address = db.Column(db.Text, nullable=True)
    place_of_receipt = db.Column(db.String(100), nullable=True)
    place_of_delivery = db.Column(db.String(100), nullable=True)
    freight_terms = db.Column(db.String(100), nullable=True)
    general_description = db.Column(db.Text, nullable=True)
    general_terms = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Booked') # Booked / In Transit / Delivered / Arrival Notice Sent
    
    # Shipment Tracking Details
    mbl_number = db.Column(db.String(100), nullable=True)
    hbl_number = db.Column(db.String(100), nullable=True)
    vessel_name = db.Column(db.String(100), nullable=True)
    voyage_number = db.Column(db.String(50), nullable=True)
    eta_pod = db.Column(db.DateTime, nullable=True)
    
    etd = db.Column(db.DateTime, nullable=True)
    is_si_submitted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cargo_items = db.relationship('CargoItem', backref='booking', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('BookingAttachment', backref='booking', lazy=True, cascade="all, delete-orphan")
    tracking_events = db.relationship('TrackingEvent', backref='booking', lazy=True, cascade="all, delete-orphan")
    shipping_instruction = db.relationship('ShippingInstruction', backref='booking', uselist=False, cascade="all, delete-orphan")
    
    # New relationships for Phase 1-3
    payment_status = db.Column(db.String(20), default='UNPAID') # UNPAID / PENDING / CONFIRMED
    edi_pre_alert = db.relationship('EdiPreAlert', back_populates='booking', uselist=False, cascade="all, delete-orphan")
    arrival_notices = db.relationship('ArrivalNotice', back_populates='booking', lazy=True, cascade="all, delete-orphan")
    proforma = db.relationship('ProformaInvoice', back_populates='booking', uselist=False, cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', back_populates='booking', lazy=True, cascade="all, delete-orphan")

class CargoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    # LCL specific
    quantity = db.Column(db.Integer, nullable=True)
    package_type = db.Column(db.String(50), nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    volume_cbm = db.Column(db.Float, nullable=True)
    length = db.Column(db.Float, nullable=True)
    width = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    uom = db.Column(db.String(10), nullable=True) # cm, m, inch
    # FCL specific
    container_count = db.Column(db.Integer, nullable=True)
    container_type = db.Column(db.String(50), nullable=True) # 20' ST, 40' HC etc.
    # Common
    hs_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    # IMO fields
    is_imo = db.Column(db.Boolean, default=False)
    un_number = db.Column(db.String(20), nullable=True)
    packing_group = db.Column(db.String(20), nullable=True)
    imo_class = db.Column(db.String(20), nullable=True)
    # SI specific fields per item
    container_no = db.Column(db.String(50), nullable=True)
    seal_no = db.Column(db.String(50), nullable=True)
    marks_numbers = db.Column(db.Text, nullable=True)

class BookingAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)

class TrackingEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ShippingInstruction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    
    # Parties
    shipper = db.Column(db.Text)
    consignee = db.Column(db.Text)
    notify_party = db.Column(db.Text)
    also_notify = db.Column(db.Text)
    shipper_reference = db.Column(db.String(100))
    
    # Vessel Details
    vessel_name = db.Column(db.String(100))
    voyage = db.Column(db.String(100))
    
    # Documentation
    freight_term = db.Column(db.String(50)) # Prepaid / Collect
    place_of_issue = db.Column(db.String(100))
    document_type = db.Column(db.String(50)) # Original / Express
    num_originals = db.Column(db.Integer, default=3)
    num_copies = db.Column(db.Integer, default=0)
    
    # Weights & VGM
    total_gross_weight = db.Column(db.Float)
    net_weight = db.Column(db.Float)
    tare_weight = db.Column(db.Float)
    vgm_provided_by = db.Column(db.String(50)) # Shipper / Forwarder
    weighing_method = db.Column(db.String(50)) # Method 1 / Method 2
    vgm_value = db.Column(db.Float)
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
class EdiPreAlert(db.Model):
    __tablename__ = 'edi_pre_alerts'
    id = db.Column(db.Integer, primary_key=True)
    mbl_number = db.Column(db.String(50), nullable=False)
    hbl_number = db.Column(db.String(50), nullable=False)
    vessel_name = db.Column(db.String(100))
    voyage_number = db.Column(db.String(50))
    port_of_loading = db.Column(db.String(100))
    port_of_discharge = db.Column(db.String(100))
    eta_pod = db.Column(db.DateTime)
    shipper_name = db.Column(db.String(200))
    consignee_name = db.Column(db.String(200))
    cargo_description = db.Column(db.Text)
    weight_kg = db.Column(db.Float)
    volume_cbm = db.Column(db.Float)
    source_type = db.Column(db.String(20))   # API / SFTP / file
    raw_payload = db.Column(db.JSON)
    parse_status = db.Column(db.String(20))   # parsed / quarantined / error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    booking = db.relationship('Booking', back_populates='edi_pre_alert')

class ArrivalNotice(db.Model):
    __tablename__ = 'arrival_notices'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    recipient_type = db.Column(db.String(30))   # consignee / broker / agent / trucker
    recipient_name = db.Column(db.String(200))
    recipient_email = db.Column(db.String(200))
    language = db.Column(db.String(5), default='en')    # en / fr / de
    pdf_path = db.Column(db.String(500))
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    send_status = db.Column(db.String(20), default='pending')   # pending / sent / delivered / failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    booking = db.relationship('Booking', back_populates='arrival_notices')

class ProformaInvoice(db.Model):
    __tablename__ = 'proforma_invoices'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    charge_lines = db.Column(db.JSON)         # list of {description, amount, currency}
    subtotal = db.Column(db.Float)
    taxes = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')    # EUR / USD
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    payment_status = db.Column(db.String(20), default='UNPAID')   # UNPAID / PENDING / CONFIRMED
    payment_reference = db.Column(db.String(100))  # SWIFT / bank ref
    payment_confirmed_at = db.Column(db.DateTime)
    confirmed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    booking = db.relationship('Booking', back_populates='proforma')
    final_invoice = db.relationship('Invoice', back_populates='proforma', uselist=False)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    proforma_id = db.Column(db.Integer, db.ForeignKey('proforma_invoices.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    invoice_number = db.Column(db.String(30), unique=True)  # AXEGLOBAL/2025/0042
    charge_lines = db.Column(db.JSON)
    total_amount = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_tax_invoice = db.Column(db.Boolean, default=True)
    pdf_path = db.Column(db.String(500))
    sent_at = db.Column(db.DateTime)
    
    booking = db.relationship('Booking', back_populates='invoices')
    proforma = db.relationship('ProformaInvoice', back_populates='final_invoice')

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50)) # Booking, Invoice, etc.
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')

# ==========================================
# PHASE 4: SOA, JOBS & INVOICE RECONCILIATION
# ==========================================

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(100), unique=True, nullable=False)
    equipment = db.Column(db.String(100))
    type = db.Column(db.String(100), default='IMPORT SEA')
    job_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='OPEN')
    incoterms = db.Column(db.String(100))
    category = db.Column(db.String(100), default='FCL - FULL')
    office = db.Column(db.String(100))
    user_profile = db.Column(db.String(100))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    estimates = db.relationship('EstimateItem', backref='job', lazy=True, cascade="all, delete-orphan")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EstimateItem(db.Model):
    __tablename__ = 'estimate_items'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    item_type = db.Column(db.String(20), nullable=False) # 'COST' or 'REVENUE'
    code = db.Column(db.String(50))
    invoice_number = db.Column(db.String(100))
    description = db.Column(db.String(500), nullable=False)
    calc_type = db.Column(db.String(50), default='manual')
    quantity = db.Column(db.Float, default=1.0)
    amount = db.Column(db.Float, default=0.0) # Unit price
    total = db.Column(db.Float, default=0.0) # Qty * Amount
    currency = db.Column(db.String(10), default='EUR')
    entity_for = db.Column(db.String(200)) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VendorInvoice(db.Model):
    __tablename__ = 'vendor_invoices'
    id = db.Column(db.Integer, primary_key=True)
    supplier = db.Column(db.String(200), nullable=False)
    supplier_code = db.Column(db.String(50))
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    invoice_type = db.Column(db.String(50), default='Invoice') 
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='EUR')
    user_group = db.Column(db.String(100))
    
    net_weight = db.Column(db.Float)
    gross_weight = db.Column(db.Float)
    vat_amount = db.Column(db.Float, default=0.0)
    vat_code = db.Column(db.String(50))
    
    notes = db.Column(db.Text)
    pdf_path = db.Column(db.String(500))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    references = db.relationship('VendorInvoiceReference', backref='vendor_invoice', lazy=True, cascade="all, delete-orphan")
    items = db.relationship('VendorInvoiceItem', backref='vendor_invoice', lazy=True, cascade="all, delete-orphan")

    match_status = db.Column(db.String(100), default='PENDING')
    matched_job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True)

class VendorInvoiceItem(db.Model):
    __tablename__ = 'vendor_invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('vendor_invoices.id'), nullable=False)
    
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10))
    
    charge_code = db.Column(db.String(50))
    vat_code = db.Column(db.String(50))
    vat_perc = db.Column(db.Float)
    
    vendor_code = db.Column(db.String(50))
    vendor_name = db.Column(db.String(200))
    
    job_id = db.Column(db.String(100))
    master_id = db.Column(db.String(100))
    m_bl_no = db.Column(db.String(100))
    h_bl_no = db.Column(db.String(100))
    container_no = db.Column(db.String(100))
    awb_no = db.Column(db.String(100))

class VendorInvoiceReference(db.Model):
    __tablename__ = 'vendor_invoice_references'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('vendor_invoices.id'), nullable=False)
    ref_type = db.Column(db.String(50))
    ref_value = db.Column(db.String(100))
    amount = db.Column(db.Float, default=0.0)

class ReceivedPDF(db.Model):
    __tablename__ = 'received_pdfs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email_message_id = db.Column(db.String(200), unique=True)
    sender_email = db.Column(db.String(200))
    subject = db.Column(db.String(500))
    filename = db.Column(db.String(300))
    local_path = db.Column(db.String(500))
    received_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theme_color = db.Column(db.String(50), default='blue') # blue, green, teal, purple, orange
    logo_path = db.Column(db.String(255), default='img/logo.png')
    login_banner_path = db.Column(db.String(255), default='img/login_hero.png')
    default_layout = db.Column(db.String(50), default='sidebar') # sidebar, topbar
