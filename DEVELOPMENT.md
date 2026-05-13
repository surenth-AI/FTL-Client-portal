<<<<<<< HEAD
# AXEGLOBAL Demo S1 - Development Documentation

## Project Overview
AXEGLOBAL Demo S1 is a modular Freight Forwarding and Logistics Portal designed to streamline the booking, tracking, and management of LCL (Less than Container Load) and FCL (Full Container Load) shipments. The system features a robust multi-vendor rate import engine, a multi-step booking workflow, and a specialized Shipping Instruction (SI) submission system.
=======
# FTL Demo S1 - Development Documentation

## Project Overview
FTL Demo S1 is a modular Freight Forwarding and Logistics Portal designed to streamline the booking, tracking, and management of LCL (Less than Container Load) and FCL (Full Container Load) shipments. The system features a robust multi-vendor rate import engine, a multi-step booking workflow, and a specialized Shipping Instruction (SI) submission system.
>>>>>>> 4bf60d4 (feat: Major aesthetic overhaul, pagination, multi-language architecture, and dispatch command interface integration)

## Tech Stack
- **Framework**: [Flask](https://flask.palletsprojects.com/) (Python 3.x)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) with SQLite (Modular and easily swappable)
- **Forms**: Flask-WTF / WTForms
- **Authentication**: Flask-Login (Role-Based Access Control)
- **Data Processing**: [Pandas](https://pandas.pydata.org/) (for advanced Excel rate parsing)
- **Frontend**: Jinja2 Templates, HTML5, CSS3, Vanilla JavaScript

## Project Structure
```text
<<<<<<< HEAD
AXEGLOBAL Demo S1/
=======
FTL Demo S1/
>>>>>>> 4bf60d4 (feat: Major aesthetic overhaul, pagination, multi-language architecture, and dispatch command interface integration)
├── app/                    # Core application package
│   ├── models/             # Database models (SQLAlchemy)
│   ├── routes/             # Blueprint-based routing (Auth, Admin, Customer, Tracking)
│   ├── services/           # Business logic (Excel Import Engine, Rate Engine)
│   ├── static/             # Assets (CSS, Images, JS)
│   └── templates/          # HTML templates (Jinja2)
├── scripts/                # Utility scripts for data migration, analysis, and maintenance
├── uploads/                # Directory for uploaded SI documents and Excel rates
├── config.py               # Environment and app configuration
└── app.py                  # Application entry point (Factory Pattern)
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- `pip` (Python package manager)

### 2. Installation
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Initialization
<<<<<<< HEAD
The application uses a Factory Pattern. On the first run, it will automatically create the SQLite database (`axeglobal.db`) and seed a default admin user.
=======
The application uses a Factory Pattern. On the first run, it will automatically create the SQLite database (`ftl.db`) and seed a default admin user.
>>>>>>> 4bf60d4 (feat: Major aesthetic overhaul, pagination, multi-language architecture, and dispatch command interface integration)

```bash
python app.py
```
**Default Admin Credentials:**
<<<<<<< HEAD
- Email: `admin@axeglobal.com`
=======
- Email: `admin@ftl.com`
>>>>>>> 4bf60d4 (feat: Major aesthetic overhaul, pagination, multi-language architecture, and dispatch command interface integration)
- Password: `admin123`

---

## Core Modules & Features

### 1. Multi-Vendor Excel Import Engine (`app/services/excel_importer.py`)
This is a critical component that allows admins to upload rate sheets from different NVOCCs (Non-Vessel Operating Common Carriers). The engine uses Pandas to detect the file format and parse the data accordingly.

- **Supported Formats**:
    - **Nordic**: Parses "LCL Export Rates" sheets where origins and destinations are mapped across columns and rows.
    - **CLG Hamburg**: Deep imports rates by summing multiple surcharge columns (EU ETS, BAF, Panama, etc.) from the "Eingabemaske Raten" sheet.
    - **Team Freight**: Cross-references ocean freight rates with a dynamic surcharge lookup from separate sheets.

### 2. Booking Workflow (`app/routes/customer.py`)
Provides a multi-step experience for customers:
1. **Search & Quote**: Users search for rates by origin/destination.
2. **Booking Selection**: Choice between LCL and FCL.
3. **Cargo Details**: Dynamic entry for multiple cargo items, including dimensions, weight, and HAZMAT (IMO) status.
4. **Finalization**: Confirmation of terms and pickup details.

### 3. Shipping Instructions (SI)
After a booking is "Booked", users can submit detailed Shipping Instructions. This includes:
- **Party Details**: Shipper, Consignee, Notify Party.
- **Vessel Information**: Vessel name and Voyage.
- **VGM (Verified Gross Mass)**: Submission of weight details per SOLAS requirements.

### 4. Tracking System (`app/routes/tracking.py`)
Allows users to view a timeline of events for their shipments. The system supports multiple events per booking (e.g., "Received at Warehouse", "Vessel Arrived").

---

## Database Models (`app/models/models.py`)

| Model | Description |
| :--- | :--- |
| **User** | Manages `admin` and `customer` accounts. |
| **Rate** | Stores imported freight rates, including surcharges and validity. |
| **Booking** | The central shipment record, linked to a User and multiple CargoItems. |
| **CargoItem** | Individual line items within a booking (dimensions, IMO details). |
| **ShippingInstruction** | Extended details for documentation (Parties, Vessel, VGM). |
| **TrackingEvent** | Log of status updates for a shipment. |

---

## Utility Scripts (`scripts/`)
The project includes a suite of maintenance scripts:
- `reupload_all.py`: Re-runs the Excel import engine on all files in the `uploads/` folder.
- `db_clean_execute.py`: Utility for cleaning up the database.
- `analyse_destinations.py`: Analyzes rate coverage across different ports.
- `seed_singapore_la.py`: Seeds specific demo data for Singapore and Los Angeles routes.

## Development Guidelines
- **Blueprints**: Always use Blueprints for new modules to maintain separation of concerns.
- **Services**: Heavy logic (like Excel parsing or complex calculations) should reside in `app/services/`.
- **Styling**: Use the existing design system in `app/static/css/`. Ensure mobile responsiveness for the tracking and booking dashboards.
