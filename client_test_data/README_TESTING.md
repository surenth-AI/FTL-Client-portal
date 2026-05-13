# AxeGlobal Logistics - Client Test Data Pack

Welcome to the official testing suite for the AxeGlobal Unified Platform. Use these files to demonstrate the power of our AI-driven logistics intelligence.

## 📁 Directory Structure & Test Cases

### 1. 📂 Vendor_Invoices/
*   **Purpose**: Test the **AP Invoice Processing** module.
*   **Action**: Go to the AP dashboard and upload these PDFs using either the **AI Extraction** or **Manual Upload** portal.
*   **What to look for**: Watch as Gemini extracts line items, quantities, and totals with 99%+ accuracy.

### 2. 📂 SOA_Statements/
*   **Purpose**: Test the **SOA Reconciliation** (Statement Audit) feature.
*   **File**: `Vendor_Statement_Audit_Sample.xlsx`
*   **Action**: In the SOA Reconciliation dashboard, upload this file.
*   **Expected Result**: You will see a mix of "Matched" and "Mismatch" results. The system is pre-seeded with jobs that correspond to the "Job No." column in this spreadsheet.

### 3. 📂 EDI_PreAlerts/
*   **Purpose**: Test **EDI Manifest Ingestion**.
*   **Action**: In the Agent Dashboard or EDI section, upload these Excel files.
*   **What to look for**: The system will use AI to read the manifest and automatically create structured Booking entries.

### 4. 📂 Rates/
*   **Purpose**: Test the **Freight Rates Intelligence** feature.
*   **Action**: Upload this sheet to the Rates section to populate the global price list.

---
**Note**: All data provided here is synthetic and designed specifically for demonstrating the AxeGlobal platform's automated workflows.
