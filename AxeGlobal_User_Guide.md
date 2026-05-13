# 🌐 AxeGlobal Unified Platform: Executive User Guide

Welcome to the future of logistics management. This guide is designed for logistics professionals who want to leverage AI and automation to eliminate manual data entry and gain 100% visibility over their supply chain.

---

## 🔐 Access Credentials
For this demonstration, use the following credentials. All accounts use the same password.

| User Role | Login Email | Password |
| :--- | :--- | :--- |
| **System Administrator** | `admin1@axeglobal.com` | `admin123` |
| **Logistics Agent** | `agent001@axeglobal.com` | `admin123` |
| **End Customer** | `customer@axeglobal.com` | `admin123` |

---

## 🏗️ Role-Based Walkthrough

### 1. 👔 System Administrator (Control Tower)
The Administrator has full visibility and control over financial auditing and global rates.

#### A. AP Invoice Processing (AI-Powered Audit)
*   **Logistics Context**: Eliminate the manual entry of vendor invoices (MSC, Maersk, etc.).
*   **How to Demo**:
    1.  Navigate to **AP Invoice Processing**.
    2.  Locate the **"AI Financial Extraction"** section.
    3.  Upload any file from the **Vendor_Invoices** folder (e.g., `INV-TEST-1000.pdf`).
    4.  **The Wow Factor**: Watch the "Data Intelligence Dashboard" open in a split-screen view. On the left, you'll see the extracted line items, taxes, and totals; on the right, you'll see the original digital document.
    
#### B. SOA Reconciliation (Statement Audit)
*   **Logistics Context**: Automatically cross-reference your internal ledger against a carrier's monthly Statement of Account (SOA).
*   **How to Demo**:
    1.  Navigate to **SOA Reconciliation**.
    2.  Upload the file: `Vendor_Statement_Audit_Sample.xlsx` (found in the **SOA_Statements** folder).
    3.  **The Wow Factor**: The system will instantly highlight "Matched" items in green and "Mismatches" in red. This saves hours of manual Excel comparison.

#### C. Rates Sheet & Intelligence
*   **Logistics Context**: Centralize your global freight rates for instant quoting.
*   **How to Demo**:
    1.  Go to **Rates Sheet**.
    2.  Upload `Global_Ocean_Rates_2026.xlsx` (found in the **Rates** folder).
    3.  **The Wow Factor**: All rates are now searchable and indexed, providing a "Single Source of Truth" for your pricing.

---

### 2. 🚢 Logistics Agent (Operations)
The Agent focuses on moving data from carriers and manifests into the system.

#### A. EDI Manifest Ingestion
*   **Logistics Context**: Turning messy Excel manifests from shipping lines into structured bookings without typing.
*   **How to Demo**:
    1.  Login as the **Agent**.
    2.  Go to **Upload EDI**.
    3.  Upload `PreAlert_Manifest_Sample.xlsx` (found in the **EDI_PreAlerts** folder).
    4.  **The Wow Factor**: Gemini AI reads the manifest, identifies the MBL, HBL, and Container numbers, and automatically populates the system's "Shipment Intelligence" log.

---

### 3. 📦 End Customer (Visibility)
The Customer enjoys a premium, self-service experience with 24/7 tracking.

#### A. Live Tracking & Visibility
*   **Logistics Context**: Real-time monitoring of cargo milestones.
*   **How to Demo**:
    1.  Login as the **Customer**.
    2.  Go to **Live Tracking**.
    3.  Enter any container number (e.g., `AXGU998877`).
    4.  **The Wow Factor**: See a beautiful, pulsing timeline showing the journey from Shanghai to Rotterdam, with active status markers for transshipment in Singapore.

#### B. New Booking Portal
*   **Logistics Context**: Digital request for FCL/LCL or Air shipments.
*   **How to Demo**:
    1.  Go to **New Booking**.
    2.  Select **Sea Freight (FCL)**.
    3.  Fill in the origin and destination.
    4.  **The Wow Factor**: A clean, intuitive form that replaces email-based booking requests, instantly notifying the operations team.

---

## 📁 Sample Data Guide
All files mentioned above are located in the **`client_test_data`** folder.

*   **Vendor_Invoices**: High-fidelity PDF documents for AI ingestion.
*   **SOA_Statements**: Large Excel ledgers for financial reconciliation testing.
*   **EDI_PreAlerts**: Manifest files for automated booking creation.
*   **Rates**: Master price lists for ocean freight.

---

## 💡 Pro-Tip for the Demo
When showing the **AP Invoice Processing** detail view, explain to the client that the system doesn't just "read text"—it **understands logistics concepts** like THC, Ocean Freight, and VAT codes, allowing for a truly "Autonomous Audit."
