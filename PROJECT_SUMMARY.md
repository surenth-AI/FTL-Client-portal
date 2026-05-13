# Fast Transit Line (FTL) Enterprise Logistics Platform
## Comprehensive Project Governance & Operational Framework

This document provides a definitive overview of the FTL platform's governance model, organizational structure, and operational workflows. It is intended for stakeholders and enterprise partners to understand the security, authorization, and process controls that ensure reliable global logistics management.

---

## 1. Multi-Tiered User Roles & Permission Matrix

The FTL platform employs a Role-Based Access Control (RBAC) system designed to mirror the structure of a global freight forwarding organization.

### 1.1 Executive & Administrative Roles

#### **Super Admin (System Governance)**
- **Scope**: Platform-wide ownership.
- **Responsibilities**:
    - Infrastructure monitoring and system-wide configuration.
    - Creating and managing Admin and Super Admin accounts.
    - Reassigning personnel between departments (e.g., moving an executive from Import to Export).
- **Authorization**: Unrestricted access to all data silos and configuration panels.

#### **Admin (Operational Management)**
- **Scope**: Regional or branch-level management.
- **Responsibilities**:
    - Overseeing the registration pipeline for new business partners.
    - Strategic rate management and carrier relations.
    - High-level shipment intelligence and performance auditing.
- **Authorization**: Full authority over operational and financial approvals; can override departmental assignments to prevent workflow bottlenecks.

### 1.2 Specialized Operational Roles (Internal Staff)

#### **Finance Executive (Department: Finance)**
- **Core Function**: Financial risk assessment and partner onboarding.
- **Authorization**: 
    - Exclusively responsible for the "Finance Approval" stage of new company registration.
    - Verifies VAT/Tax identifiers and performs creditworthiness checks.
    - **Restriction**: Cannot activate shipments or modify freight rates.

#### **Operations Executive (Departments: Export / Import / Warehouse)**
- **Core Function**: Execution of the physical and logistical movement of cargo.
- **Authorization**:
    - **Export/Import**: Responsible for the "Operations Activation" stage of company onboarding.
    - **Warehouse**: Updates cargo status at local collection points and distribution hubs.
    - **Specific Assignment**: Can only activate companies or shipments that have been specifically assigned to them by a Manager or Finance staff.
- **Restriction**: Cannot bypass financial approval steps or access internal financial records of other partners.

### 1.3 External Partner Roles

#### **Customer (Enterprise Client)**
- **Scope**: Company-specific portal access.
- **Responsibilities**:
    - Submitting booking requests based on live freight rates.
    - Managing cargo documentation and Shipping Instructions (SI).
    - Monitoring real-time tracking milestones.
- **Authorization**: Isolated to their own company's data silo. 
- **Restriction**: Strictly prohibited from viewing rates, bookings, or data belonging to other enterprise clients.

---

## 2. The Integrated Approval & Onboarding Workflow

The FTL platform utilizes a "Gatekeeper" model to ensure every business partner is verified through multiple specialized departments.

### 2.1 The Three-Gate Company Activation Process
1.  **Gate 1: Financial Audit**: When a new company registers, they enter a `Pending Finance` state. A Finance Executive must verify their VAT/EORI credentials and legal standing.
2.  **Gate 2: Personnel Assignment**: Upon financial clearance, the system requires the Finance Lead to assign the account to a specific **Operations Executive** based on the primary trade route or cargo type.
3.  **Gate 3: Technical Activation**: The assigned Operations staff performs a final review of the cargo requirements and activates the account. This triggers the generation of the unique **FTL Code** (e.g., `FTL-DE-052`), which serves as the permanent identifier for all future shipments.

### 2.2 Domain-Verified Team Expansion
To allow large organizations to scale their use of the platform securely:
- New users from an existing company can request access.
- **Authorization Condition**: The system automatically rejects any join request if the user's email domain (e.g., `@global-logistics.com`) does not match the verified domain of the parent company.

---

## 3. Data Governance & Privacy Standards

### **Multi-Tenancy Siloing**
The FTL platform architecture ensures that data is partitioned at the source. There is no possibility of cross-contamination between different enterprise clients, even if they share the same trade routes or carriers.

### **Audit Trail & Accountability**
Every change in status (e.g., from `Pending` to `Active`) is logged with a timestamp and the unique ID of the staff member who authorized the change. This provides a complete audit trail for compliance and quality control.

### **Shipment Intelligence (BI)**
The platform aggregates operational data into a high-level intelligence dashboard for Admins:
- **Volume Trends**: Analysis of CBM (Cubic Meters) and Weight across global routes.
- **Hazardous Cargo Ratios**: Monitoring of IMO-classed cargo to ensure safety compliance.
- **Operational Health**: Tracking of documentation delays and invoicing issues.

---

## 4. Summary of Authorization Conditions

| Action | Required Role | Mandatory Condition |
| :--- | :--- | :--- |
| **User Login** | Any | Account must be in `Active` status. |
| **Finance Approval** | Finance Exec / Admin | Company must have valid VAT/EORI data. |
| **Ops Activation** | Assigned Ops / Admin | Company must have prior Finance Approval. |
| **Booking Creation** | Customer | Must be linked to an `Active` Company. |
| **Rate Management** | Admin / Super Admin | None (Management override). |
| **Staff Reassignment** | Super Admin | Targeted user must be internal staff. |

---
**Document Status**: Final  
**Confidentiality**: Enterprise Restricted  
**Version**: 2.1
