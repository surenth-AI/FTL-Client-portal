# Fast Transit Line (FTL) Client Portal — High Performance Setup

This application uses a dual-engine architecture designed for **instant, sub-second page transitions**:
1. **Flask REST API (Port 5005)**: Handles authentication, session security, database persistence, and communicates with remote RealNexus ERP APIs.
2. **React + SWR Frontend (Port 3000)**: Modern Single Page Application with client-side **Stale-While-Revalidate (SWR)** caching, eliminating full-page reloads and white screen freezes.

---

## ⚡ How to Run

### Step 1: Start the Flask Backend (Port 5005)
Open a terminal and run:
```powershell
cd d:\FTL-DEV
python app.py
```
*(Runs at `http://127.0.0.1:5005`)*

---

### Step 2: Start the React Frontend (Port 3000)
Open a second terminal and run:
```powershell
cd d:\FTL-DEV\frontend
npm run dev
```
*(Runs at `http://localhost:3000`)*

Open **`http://localhost:3000`** in your browser. All API requests are automatically proxied to Flask.

---

## 🔑 Login Credentials

### 1. Customer Account
* **Email**: `customer@demo.com`
* **Password**: `Customer@123456!`
* **Role**: Customer (full access to Dashboard, Rate Search, New Booking, Live Shipments, and Saved Quotes)

### 2. Administrator Account
* **Email**: `admin@axeglobal.com`
* **Password**: `Admin@123456!`
* **Role**: Customer Admin

---

## 🚀 Performance Optimizations Implemented

1. **SWR Client-Side In-Memory Caching**:
   - **0 ms Page Switching**: When clicking between Dashboard, Shipments, Quotes, and Rates, previously visited pages display **instantaneously from memory** without blank screens or loading spinners.
   - **Silent Background Revalidation**: While you view the cached screen, SWR verifies with the server in the background and silently updates values only if new data arrived.
   - **Smooth Tab Navigation**: Switching between "In Transit", "Booked", and "Delivered" tabs does not refetch from the server.

2. **Backend In-Memory Caching (`d:\FTL-DEV\app\routes\customer.py`)**:
   - **Dashboard Stats**: Cached in memory for 30 seconds (returns in ~1 ms instead of 800 ms).
   - **Shipments List**: Cached per page for 45 seconds to eliminate repetitive N+1 external API calls.
   - **Master Ports & Code Lists**: Cached for 1 hour to prevent blocking form loads on New Booking and Rates.

3. **CORS & Session Cookie Integration**:
   - `Flask-CORS` configured with `supports_credentials=True` for seamless authentication with cross-origin requests.
