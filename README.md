# AxeGlobal Logistics Customer Portal

A complete end-to-end logistics management system built with Python Flask.

## Features
- **Smart Rate Engine**: Automatically ranks carriers by Cost, Speed (Transit Days), and a balanced "Best" score.
- **Admin Dashboard**: Upload rate sheets via CSV, manage existing rates, and update shipment tracking status.
- **Customer Portal**: Search for rates, compare recommendations (color-coded), book shipments, and track them via a visual timeline.
- **REST API**: Tracking endpoint available at `/api/tracking/<id>`.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Access the Portal**:
   Open your browser and go to `http://127.0.0.1:5000`

## Demo Credentials
- **Admin**: `admin@axeglobal.com` / `admin123`
- **Customer**: Register a new account via the `/register` page.

## Sample Rate Sheet
A `sample_rates.csv` file is included in the root directory for testing the Admin upload feature.
