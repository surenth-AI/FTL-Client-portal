# AxeGlobal Logistics (AXEGLOBAL) — Unified Freight Management Platform

> **Asia → Africa → Europe Consolidation | End-to-End Logistics Portal**
> Confidential — AxeGlobal Logistics Internal Document

---

## Platform at a Glance

| Metric | Value |
|--------|-------|
| Functional modules | 7 (4 existing + 3 new) |
| Trade lanes | Asia → Africa → Europe |
| User roles | Admin & Customer |
| Flask blueprints | 5 (4 existing + 1 new EDI) |
| Shipment types | LCL & FCL |
| Architecture | Python / Flask Factory Pattern |

---

## 1. Executive Summary

The **AxeGlobal Logistics (AXEGLOBAL) Customer Portal** is a comprehensive, end-to-end logistics management and freight forwarding platform. Originally designed to serve consolidation traffic on Asia–Africa trade lanes, the platform is now being extended to re-enter the European market in partnership with a strong Chinese NVOCC.

The combined platform covers the **full shipment lifecycle**: from rate search and booking, through shipping instructions and documentation, to EDI pre-alert ingestion, multi-party arrival notices, proforma invoicing, and final bill of lading release upon payment confirmation. Every module is built on a single unified Flask codebase, sharing one database and one authentication system.

For a **tech team**, the platform is a modular Python/Flask monolith with clearly separated blueprints — meaning new modules plug in without disturbing existing functionality.

For an **operations team**, it is a single portal that replaces email chains, spreadsheets, and manual document generation with automated, traceable workflows.

---

## 2. Platform Architecture

AXEGLOBAL is built using the **Flask Factory Pattern** — a well-established architectural approach where the application is divided into independent Blueprint modules, each responsible for a distinct functional area. This design means the application can grow (new modules can be added) without touching existing code, and each module can be tested and deployed independently.

### 2.1 Flask Blueprint Modules

| Blueprint | Route prefix | Responsibility | Status |
|-----------|-------------|----------------|--------|
| **Auth** | `/auth` | Login, logout, registration, session management | ✅ Existing |
| **Admin** | `/admin` | Rate uploads, shipment status control, user admin | ✅ Existing |
| **Customer** | `/customer` | Search, quote, book, submit SI, view shipments | ✅ Existing |
| **Tracking** | `/tracking` | Visual timeline, event updates, status history | ✅ Existing |
| **EDI** | `/edi` | Pre-alert ingest, parse, auto-create shipment record | 🆕 New |
| **Notices** | `/notices` | Multi-party arrival notices, PDF generation, email | 🆕 New |
| **Billing** | `/billing` | Revenue Invoice invoice, payment gate, B/L release | 🆕 New |

### 2.2 Technical Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3 / Flask | Web framework, routing, business logic, blueprint architecture |
| **ORM / DB** | SQLAlchemy / SQLite | Database models, migrations, relationships *(upgrade to PostgreSQL for production)* |
| **Data parsing** | Pandas | Excel/CSV rate sheet ingestion from NVOCCs; extendable for EDI flat file parsing |
| **Templates** | Jinja2 | Server-side HTML rendering for customer portal, admin dashboard, document PDFs |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Responsive premium UI, no heavy framework |
| **PDF engine** | WeasyPrint / ReportLab | Arrival notice and invoice PDF generation from Jinja2 templates *(to be added)* |
| **Email** | SMTP / SendGrid | Automated dispatch of arrival notices, invoices, and release documents |
| **Scripts** | Python utilities | DB migration, coverage analysis, database maintenance and seeding |

### 2.3 Project Structure

```
app/
├── __init__.py              # App factory (create_app)
├── models/                  # SQLAlchemy models
│   ├── user.py
│   ├── booking.py
│   ├── rate.py
│   ├── tracking_event.py
│   ├── edi_pre_alert.py     # 🆕 New
│   ├── arrival_notice.py    # 🆕 New
│   └── proforma_invoice.py  # 🆕 New
├── services/                # Core business logic
│   ├── excel_importer.py    # Existing rate sheet parser
│   ├── edi_parser.py        # 🆕 New EDI parser
│   ├── notice_service.py    # 🆕 New notice dispatcher
│   └── billing_service.py   # 🆕 New billing engine
├── blueprints/
│   ├── auth/
│   ├── admin/
│   ├── customer/
│   ├── tracking/
│   ├── edi/                 # 🆕 New
│   ├── notices/             # 🆕 New
│   └── billing/             # 🆕 New
├── templates/
│   ├── arrival_notice.html  # 🆕 New PDF template
│   └── proforma_invoice.html# 🆕 New PDF template
scripts/                     # Utility scripts
```

---

## 3. Existing Core Modules

The four pillars below are fully built and operational in the current AXEGLOBAL platform. They form the foundation on which the new consolidation modules are layered.

---

### Module 01 — Smart Rate Engine

> *Multi-vendor pricing, surcharge calculation, carrier ranking*

The rate engine is the commercial heart of the platform. It solves a real problem in freight forwarding: every NVOCC (carrier) sends rate sheets in their own Excel format, with different column names, structures, and surcharge conventions. Rather than manually re-entering these rates, AXEGLOBAL imports them directly.

| Feature | Description | Type |
|---------|-------------|------|
| **Excel import** | Pandas-powered parser handles non-standard NVOCC rate sheets from Nordic, CLG Hamburg, Team Freight and others. Each carrier's format is mapped to a normalised internal schema. | Automated |
| **Surcharge calculation** | Automatically sums ocean freight with all applicable surcharges: BAF (Bunker Adjustment Factor), EU ETS (emissions trading surcharge), ISPS, documentation fees, and any carrier-specific additions. | Automated |
| **Carrier ranking** | Presents results ranked by three criteria — lowest Cost, shortest Transit Time, and a proprietary Best score that balances both factors for the customer's context. | Smart |
| **Admin rate control** | Admin dashboard allows uploading new rate files via CSV at any time. Rates are versioned so historical bookings retain their original pricing. | Admin-controlled |

**Supported carriers:** Nordic, CLG Hamburg, Team Freight *(extensible to any NVOCC)*

---

### Module 02 — Multi-Step Booking Workflow

> *Guided quote-to-booking for LCL and FCL shipments*

The booking module guides the customer through a structured multi-step process, reducing errors and ensuring all required data is captured before a booking is confirmed.

```
Step 1: Search rates
   ↓ Enter origin, destination, cargo type, ready date
Step 2: Select quote
   ↓ Choose carrier from ranked results
Step 3: Enter cargo
   ↓ Line items: dimensions, weight, pieces, HAZMAT
Step 4: Confirm booking
   ↓ Booking reference generated, admin notified
```

| Feature | Description | Type |
|---------|-------------|------|
| **Rate search** | Customer enters origin, destination, cargo type (LCL/FCL), and ready date. System queries available rates and presents ranked options with full cost breakdown. | Customer-facing |
| **Cargo entry** | Dynamic multi-line cargo entry: each line captures dimensions (L × W × H), weight, number of pieces, description, and HAZMAT/IMO class if applicable. | Dynamic |
| **LCL / FCL** | Handles both Less than Container Load (shared containers, charged by CBM/weight) and Full Container Load (dedicated container, charged per box) bookings in a single workflow. | Both modes |
| **Booking confirmation** | On confirmation, a booking reference is generated, shipment record created in the database, and the customer receives an acknowledgement. Admin is notified. | Automated |

---

### Module 03 — Shipping Instructions & Documentation

> *Post-booking SI submission, party details, VGM*

After a booking is confirmed, the customer must submit **Shipping Instructions (SI)** — the legal document that tells the carrier what to print on the Bill of Lading. AXEGLOBAL provides a structured module for this.

| Feature | Description | Type |
|---------|-------------|------|
| **Party details** | Captures full legal names and addresses for Shipper, Consignee, and Notify Party — exactly as they must appear on the Bill of Lading. Validation ensures no field is missing. | Structured |
| **Vessel / voyage** | Records vessel name, voyage number, port of loading, port of discharge, and estimated dates for the specific sailing the cargo is booked on. | Linked to booking |
| **VGM submission** | Verified Gross Mass submission per IMO SOLAS regulations — mandatory since 2016. System captures method (Method 1: weighed, Method 2: calculated) and authorized signatory. | Regulatory |
| **Document history** | All submitted SI documents are stored against the booking record with timestamps, enabling full audit trail and version control. | Audited |

> ⚠️ **Regulatory note:** VGM submission is legally mandatory under SOLAS Chapter VI, Regulation 2. Non-submission can result in cargo being off-loaded at the port of loading.

---

### Module 04 — Advanced Tracking & Admin Control

> *Visual timeline for customers, operations dashboard for admins*

The tracking module gives customers real-time visibility into their shipment status, while giving the operations team the tools to update and manage those statuses.

**Customer-facing timeline example:**
```
● Booking confirmed          Jan 10, 2025
● SI submitted               Jan 12, 2025
● Cargo received at warehouse Jan 18, 2025
● Vessel departed (Shenzhen) Jan 22, 2025
○ Vessel arrived (Hamburg)   Feb 14, 2025  ← ETA
○ Cargo released             Feb 16, 2025  ← Pending
```

| Feature | Description | Type |
|---------|-------------|------|
| **Visual timeline** | Customer sees a chronological event timeline from booking confirmation through to final cargo release. | Customer-facing |
| **Status updates** | Admin team updates shipment statuses from the admin dashboard. Each update creates a timestamped event in the tracking log, immediately visible to the customer. | Admin-controlled |
| **Role separation** | Customers see only their own shipments and public-facing event descriptions. Admins see all shipments, internal notes, and full event details. | Role-based |
| **Event extensibility** | The event model is designed for extension — new event types are added as new constants, not schema changes. | Extensible |

---

## 4. New Consolidation Modules — Europe Re-entry

The three new modules below extend AXEGLOBAL to support **inbound consolidation traffic from Asia to Europe** via the Chinese NVOCC partner. They are designed as additive Flask blueprints — the existing platform requires no changes to accommodate them.

**Overall flow of new modules:**

```
Chinese partner sends EDI pre-alert
         ↓
System auto-creates shipment record
         ↓
Arrival notices dispatched to all parties
         ↓
Revenue Invoice invoice issued to consignee
         ↓
Consignee makes payment
         ↓
Admin confirms payment in system
         ↓
B/L released + final invoice issued automatically
```

---

### Module 05 — EDI Pre-Alert Ingestion

> *Receive structured shipment data from Chinese partner automatically*

**EDI (Electronic Data Interchange)** is the industry-standard method for exchanging structured business documents between logistics companies. When the Chinese partner loads cargo at origin, they send a pre-alert EDI message containing all shipment details. AXEGLOBAL receives, parses, and acts on this message automatically — no manual data entry required.

#### What is an EDI pre-alert?

Think of it as an automated notification from your partner that says: *"I have loaded these goods onto this vessel, here are all the details."* It arrives as a structured data file — similar to a very standardised CSV or XML — and contains everything needed to create a shipment record.

**Information contained in a pre-alert:**

| Field | Description |
|-------|-------------|
| MBL number | Master Bill of Lading — the carrier's main tracking reference |
| HBL number | House Bill of Lading — your internal reference number |
| Vessel & voyage | Ship name, voyage number |
| Port of loading | Where cargo was loaded (e.g. Shenzhen, Shanghai) |
| Port of discharge | Destination port (e.g. Hamburg, Antwerp, Rotterdam) |
| ETA | Estimated arrival date at destination port |
| Shipper | Name & address of the exporting factory/company |
| Consignee | Name & address of the European buyer |
| Cargo description | What the goods are |
| Weight & volume | Kilograms and cubic metres |

#### Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Ingest endpoint** | Secure API endpoint `/edi/ingest` receives EDI files via HTTPS POST or SFTP. Supports IFTMIN, COPARN, COARRI message types and flat-file fallback. | Automated |
| **EDI parser service** | New `app/services/edi_parser.py` maps EDI fields to internal schema using Pandas. Handles non-standard field names and missing optional fields gracefully. | Robust |
| **Shipment auto-creation** | On successful parse, automatically creates a `Booking` record, an `EdiPreAlert` record (linked), and triggers the arrival notice workflow. | Automated |
| **Validation & error handling** | Validates required fields before creating records. Invalid pre-alerts are quarantined in an admin review queue with clear error descriptions. | Safe |
| **Admin pre-alert dashboard** | Lists all incoming pre-alerts with status (parsed / quarantined / manual review), source partner, vessel, ETA, and linked booking. | Admin-controlled |

#### New database model: `EdiPreAlert`

```python
class EdiPreAlert(db.Model):
    __tablename__ = 'edi_pre_alerts'

    id                = db.Column(db.Integer, primary_key=True)
    mbl_number        = db.Column(db.String(50), nullable=False)
    hbl_number        = db.Column(db.String(50), nullable=False)
    vessel_name       = db.Column(db.String(100))
    voyage_number     = db.Column(db.String(50))
    port_of_loading   = db.Column(db.String(100))
    port_of_discharge = db.Column(db.String(100))
    eta_pod           = db.Column(db.DateTime)
    shipper_name      = db.Column(db.String(200))
    consignee_name    = db.Column(db.String(200))
    cargo_description = db.Column(db.Text)
    weight_kg         = db.Column(db.Float)
    volume_cbm        = db.Column(db.Float)
    source_type       = db.Column(db.String(20))   # API / SFTP / file
    raw_payload       = db.Column(db.JSON)
    parse_status      = db.Column(db.String(20))   # parsed / quarantined / error
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    booking_id        = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    booking           = db.relationship('Booking', back_populates='edi_pre_alert')
```

---

### Module 06 — Multi-Party Arrival Notice

> *Automated notifications to all parties before cargo arrives*

In consolidation freight, a single vessel carries cargo for many different buyers. When that vessel approaches the destination port, every party involved in each shipment needs to be notified and given time to prepare. AXEGLOBAL automates this entirely — the right notice goes to the right person, automatically, at the right time.

#### Who gets notified and why?

| Recipient | Their role | What they do with the notice |
|-----------|-----------|------------------------------|
| **Consignee / buyer** | The company receiving the goods | Arranges warehouse space, staff, and inland transport for delivery day |
| **Customs broker** | Licensed agent who handles import paperwork | Begins preparing the import customs entry — needs 5–10 days before arrival |
| **Destination agent** | Your local partner at the European port | Arranges port handling, container de-stuffing, and local operations |
| **Trucking company** | Delivers cargo from port to buyer's warehouse | Books the truck and driver for collection from the port after customs clearance |

#### Why "multi" arrival notice?

- One vessel can carry cargo for **dozens of different buyers** (consolidation)
- Each buyer gets their **own personalised notice** showing only their cargo
- Each notice has the **right charge breakdown** for that specific buyer's shipment
- Different recipients get **different levels of detail** (e.g. trucker gets pickup reference, broker gets HS codes)

#### Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Recipient configuration** | Each booking has a configurable recipient list. Admin or customer sets who receives notices, with email addresses and preferred language per recipient. | Configurable |
| **PDF notice generation** | Jinja2 template renders a professional arrival notice PDF per recipient, showing only their relevant cargo — not other buyers' goods. | Per-recipient |
| **Automatic dispatch** | Notices triggered automatically X days before ETA (configurable — typically 10–14 days). No manual action required. | Automated |
| **Multi-language support** | Notice templates available in English, French, and German to serve European markets. Language selection is per-consignee. | Multilingual |
| **Delivery tracking** | System records when each notice was sent, whether delivered, and when opened. Admin sees at a glance who has and has not acknowledged. | Traceable |
| **Timeline integration** | Each notice dispatch creates a new tracking event: *Arrival notice sent to consignee*, *Arrival notice sent to customs broker*, etc. | Integrated |

#### New database model: `ArrivalNotice`

```python
class ArrivalNotice(db.Model):
    __tablename__ = 'arrival_notices'

    id               = db.Column(db.Integer, primary_key=True)
    booking_id       = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    recipient_type   = db.Column(db.String(30))   # consignee / broker / agent / trucker
    recipient_name   = db.Column(db.String(200))
    recipient_email  = db.Column(db.String(200))
    language         = db.Column(db.String(5))    # en / fr / de
    pdf_path         = db.Column(db.String(500))
    sent_at          = db.Column(db.DateTime)
    delivered_at     = db.Column(db.DateTime)
    opened_at        = db.Column(db.DateTime)
    send_status      = db.Column(db.String(20))   # pending / sent / delivered / failed
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    booking          = db.relationship('Booking', back_populates='arrival_notices')
    # Note: one booking → many ArrivalNotice records (one per recipient)
```

---

### Module 07 — Revenue Invoice, Payment Gate & B/L Release

> *Billing control — no payment, no cargo documents*

This module is the **commercial and legal control centre** of the consolidation workflow. It enforces the freight industry's most fundamental rule: the carrier (or forwarder) holds the cargo documents until charges are paid. No payment means no document means no cargo. AXEGLOBAL automates both sides — generating the invoice and enforcing the release gate.

#### The three-stage billing lifecycle

| Stage | Document | Description | Trigger |
|-------|----------|-------------|---------|
| **1** | Revenue Invoice invoice | Itemised cost estimate sent to the consignee. Marked as an estimate, not a tax invoice. Client pays against this. | Auto-generated on arrival notice dispatch |
| **2** | Payment confirmation | Admin confirms receipt of payment in the system. System unlocks the shipment record. | Admin action after bank transfer received |
| **3** | Final invoice + B/L release | Revenue Invoice converts to a legally valid tax invoice with sequential invoice number. B/L or telex release generated and emailed. | Auto-triggered on payment confirmation |

#### What charges appear on the proforma invoice?

```
Revenue Invoice — AXEGLOBAL/2025/0042
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ocean freight (LCL)      €  480.00
Origin THC (Shenzhen)    €   85.00
Destination THC (Hamburg)€  120.00
B/L documentation fee    €   45.00
Customs doc fee          €   35.00
Agency / handling fee    €   95.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL DUE                € 860.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  PROFORMA — NOT A TAX INVOICE
Payment due before cargo release
```

#### Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Charge line builder** | Pulls charge lines from the existing rate engine: ocean freight, THC, B/L fee, customs fee, agency fee. Pre-populated from the booking; admin can adjust before issuing. | From rate engine |
| **Revenue Invoice PDF generation** | Professional invoice PDF from Jinja2 template. Clearly watermarked *PROFORMA — NOT A TAX INVOICE*. Includes bank details, SWIFT/IBAN, and payment reference format. | Automated |
| **Payment gate (hard lock)** | Shipment record has a `payment_status` field: `UNPAID / PENDING / CONFIRMED`. All document release actions are blocked until status = `CONFIRMED`. No bypass. | Hard lock 🔒 |
| **Payment matching** | Admin enters the bank transfer reference when confirming payment. System stores SWIFT reference, amount, date, and confirming admin user — full audit trail. | Audited |
| **Revenue Invoice → invoice conversion** | On payment confirmation, proforma is promoted to a final invoice: sequential invoice number assigned, tax invoice status applied. Revenue Invoice is archived. | Automated |
| **B/L and telex release** | System generates the House Bill of Lading (HBL) or Telex Release instruction and emails it to the consignee and their customs broker simultaneously. | Automated |

#### New database models

```python
class ProformaInvoice(db.Model):
    __tablename__ = 'proforma_invoices'

    id                   = db.Column(db.Integer, primary_key=True)
    booking_id           = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    charge_lines         = db.Column(db.JSON)         # list of {description, amount, currency}
    subtotal             = db.Column(db.Float)
    taxes                = db.Column(db.Float)
    total_amount         = db.Column(db.Float)
    currency             = db.Column(db.String(3))    # EUR / USD
    issued_at            = db.Column(db.DateTime)
    valid_until          = db.Column(db.DateTime)
    payment_status       = db.Column(db.String(20))   # UNPAID / PENDING / CONFIRMED
    payment_reference    = db.Column(db.String(100))  # SWIFT / bank ref
    payment_confirmed_at = db.Column(db.DateTime)
    confirmed_by_id      = db.Column(db.Integer, db.ForeignKey('users.id'))

    booking              = db.relationship('Booking', back_populates='proforma')
    final_invoice        = db.relationship('Invoice', back_populates='proforma', uselist=False)


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id               = db.Column(db.Integer, primary_key=True)
    proforma_id      = db.Column(db.Integer, db.ForeignKey('proforma_invoices.id'))
    booking_id       = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    invoice_number   = db.Column(db.String(30), unique=True)  # AXEGLOBAL/2025/0042
    charge_lines     = db.Column(db.JSON)
    total_amount     = db.Column(db.Float)
    currency         = db.Column(db.String(3))
    issued_at        = db.Column(db.DateTime)
    is_tax_invoice   = db.Column(db.Boolean, default=True)
    pdf_path         = db.Column(db.String(500))
    sent_at          = db.Column(db.DateTime)

    proforma         = db.relationship('ProformaInvoice', back_populates='final_invoice')
```

---

## 5. Automation Map

One of the key design goals of the combined AXEGLOBAL platform is to automate every repetitive, data-entry, and document-generation task — leaving human attention for judgment calls, exceptions, and relationship management.

| Task | Handled by | Notes |
|------|-----------|-------|
| Receive EDI pre-alert from Chinese partner | ✅ System | API endpoint — zero human touch for clean files |
| Parse EDI and create shipment record | ✅ System | Auto in under 1 second after receipt |
| Send multi-party arrival notices | ✅ System | Triggered automatically by ETA countdown |
| Generate proforma invoice PDF | ✅ System | Pulled from rate engine, no manual calculation |
| Email invoice to consignee | ✅ System | Sent with arrival notice automatically |
| Convert proforma to final invoice | ✅ System | Triggered instantly on payment confirmation |
| Generate and send B/L / telex release | ✅ System | Emailed to consignee and broker automatically |
| Confirm payment received | 🟡 Human (admin) | Admin checks bank and marks confirmed in portal |
| Match SWIFT reference to booking | 🟡 Human (admin) | Future: bank webhook will automate this |
| Review quarantined / invalid EDI files | 🟡 Human (admin) | Admin reviews errors, corrects and re-triggers |
| Update shipment tracking events | 🟡 Human + System | Manual updates + auto events from workflow |
| Handle cargo disputes or damage claims | 🔴 Human (ops) | Requires judgment, negotiation, legal review |
| Handle customs holds or port inspections | 🔴 Human (ops) | Regulatory — always requires a human agent |
| Negotiate special rates with a client | 🔴 Human (commercial) | Relationship-based — not automatable |

**Summary:** ~70% of tasks are fully automated, ~20% require occasional human oversight, ~10% always require human judgment.

---

## 6. Implementation Roadmap

The new modules are built in three sequential phases. Each phase delivers a working, testable slice of the new functionality. Existing AXEGLOBAL operations continue uninterrupted throughout the build.

### Phase 1 — EDI Ingest & Shipment Creation
**Timeline: 2–3 weeks**

- New EDI blueprint: `app/edi/routes.py`
- EDI parser service: `app/services/edi_parser.py`
- `EdiPreAlert` SQLAlchemy model + DB migration
- Auto-create `Booking` from parsed pre-alert
- Admin UI: pre-alert list, status, manual trigger
- Error quarantine queue for invalid files

### Phase 2 — Multi-Party Arrival Notice
**Timeline: 2–3 weeks**

- `ArrivalNotice` model + recipient config per booking
- PDF template: Jinja2 → WeasyPrint
- Email dispatch service with delivery tracking
- ETA-based automatic trigger (scheduler / cron job)
- Multi-language template support (EN / FR / DE)
- Tracking timeline: new event types

### Phase 3 — Revenue Invoice, Payment Gate & B/L Release
**Timeline: 3–4 weeks**

- `ProformaInvoice` model + charge line builder from rate engine
- Invoice PDF generator (Jinja2 template)
- Payment confirmation admin workflow
- Hard payment gate on all document release actions
- Revenue Invoice → final invoice conversion
- B/L / telex release document generation + email dispatch
- Full audit log: payment reference, admin, timestamp

### Timeline Summary

| | Phase 1 | Phase 2 | Phase 3 | Total |
|-|---------|---------|---------|-------|
| **Duration** | 2–3 weeks | 2–3 weeks | 3–4 weeks | **7–10 weeks** |
| **Risk** | Low | Low | Medium | Payment matching |

> ⚠️ **Primary risk:** Payment matching. Bank references don't always match invoice numbers. Design a manual admin override from day one, and plan to automate via bank webhook later.

---

## 7. End-to-End User Journeys

### 7.1 Customer Journey (consignee in Europe)

1. **Receives arrival notice** — An email arrives with a PDF arrival notice showing their cargo details, vessel ETA, and a proforma invoice for charges due.

2. **Reviews charges** — Opens the proforma invoice PDF showing itemised charges: ocean freight, THC, B/L fee, agency fee, total in EUR.

3. **Makes bank transfer** — Transfers the proforma amount to AXEGLOBAL's bank account, including the invoice reference number in the payment description.

4. **Receives release documents** — Once payment is confirmed by AXEGLOBAL admin, receives the final invoice and the B/L / telex release automatically by email.

5. **Collects cargo** — Presents the telex release to the shipping line and delivery order to the port terminal. Cargo is released.

### 7.2 Admin / Operations Journey

1. **EDI pre-alert arrives** — System receives and parses the pre-alert from the Chinese partner. A new shipment appears in the admin dashboard automatically.

2. **Review pre-alert** — Admin checks the parsed pre-alert for accuracy. If valid, shipment moves to active. If errors, admin corrects and re-triggers.

3. **Notices auto-dispatched** — System sends arrival notices to all configured recipients 10–14 days before ETA. Admin sees delivery confirmations in the portal.

4. **Payment arrives** — Admin checks bank account, locates transfer matching the invoice reference, and marks the payment as confirmed in the portal.

5. **B/L released automatically** — System instantly generates and sends the final invoice and release documents. Admin receives a copy. Tracking timeline updated.

---

## 8. Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Additive architecture** | Every new module is a new Flask Blueprint. The existing codebase is never modified — only extended. Zero regression risk on existing LCL/FCL booking functionality. |
| **Single source of truth** | One database, one set of models, one authentication system. No data duplication between modules. |
| **Automation by default** | Every step that can be automated is automated. Humans are in the loop only for payment confirmation, exception handling, and dispute resolution. |
| **Hard payment gate** | The B/L release is programmatically blocked until `payment_status = CONFIRMED`. No UI path, no admin shortcut, no API route bypasses this check. |
| **Full audit trail** | Every action — notice sent, payment confirmed, B/L released — is timestamped and attributed to a user. Nothing happens without a log entry. |
| **Scalable data model** | The new models use standard foreign keys to the existing `Booking` model. Migrating to PostgreSQL requires only a connection string change. |

---

## 9. Glossary of Terms

| Term | Definition |
|------|------------|
| **EDI** | Electronic Data Interchange — structured digital format for exchanging business documents between logistics companies |
| **MBL** | Master Bill of Lading — the main shipping document issued by the ocean carrier (shipping line) |
| **HBL** | House Bill of Lading — a bill of lading issued by the freight forwarder (you) to the consignee |
| **LCL** | Less than Container Load — cargo that shares a container with other buyers' goods; charged by CBM/weight |
| **FCL** | Full Container Load — the buyer pays for and uses an entire container exclusively |
| **NVOCC** | Non-Vessel Operating Common Carrier — a freight company that books space on ships but doesn't own ships |
| **THC** | Terminal Handling Charge — fee charged by the port terminal for handling the container |
| **BAF** | Bunker Adjustment Factor — surcharge that adjusts for changes in fuel (bunker) prices |
| **EU ETS** | European Union Emissions Trading System — carbon surcharge applied to ships calling at EU ports since 2024 |
| **VGM** | Verified Gross Mass — mandatory declared weight of a packed container under SOLAS maritime law |
| **SOLAS** | Safety of Life at Sea — international maritime convention governing ship and cargo safety |
| **SI** | Shipping Instructions — document submitted by the shipper detailing how the Bill of Lading should be issued |
| **Revenue Invoice invoice** | A preliminary invoice sent before final charges are confirmed; marked as an estimate, not a tax document |
| **Telex release** | An electronic instruction allowing cargo release without presenting a paper Bill of Lading |
| **B/L switch** | Replacing an origin Bill of Lading with a new one issued at the destination port |
| **SWIFT** | Society for Worldwide Interbank Financial Telecommunication — global bank transfer reference system |
| **Consignee** | The party receiving the shipment — typically the buyer or importer |
| **Notify party** | A third party (often the customs broker) who is informed when the vessel arrives |
| **CBM** | Cubic metres — the unit of volume used to calculate LCL freight charges |

---

*Confidential — AxeGlobal Logistics Internal Document*
*Combined Platform Description v1.0*
