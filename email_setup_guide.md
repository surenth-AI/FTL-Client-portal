# 📧 AxeGlobal Transactional Mail Setup Guide

This guide walks you through acquiring the SMTP credentials for the three most common mail providers so you can plug them into the **AxeGlobal Admin Dashboard Settings** at `http://127.0.0.1:5000/admin/settings`.

---

## 🔑 Method 1: Gmail / Google Workspace (Recommended for dev/testing)

Gmail requires a secure **App Password** because standard passwords are blocked under modern security protocols.

### Step 1: Enable 2-Step Verification
1. Go to your **[Google Account Security Panel](https://myaccount.google.com/security)**.
2. Under "How you sign in to Google", verify that **2-Step Verification** is turned **ON**. If not, enable it.

### Step 2: Generate an App Password
1. Click into the **2-Step Verification** menu.
2. Scroll to the very bottom and click on **App passwords**.
3. Under **App name**, enter something recognizable (e.g., `AxeGlobal Portal`).
4. Click **Create**.
5. Copy the generated **16-character passcode** (e.g., `abcd efgh ijkl mnop`). *Note: This passcode only displays once!*

### Step 3: Input Settings into Admin Dashboard
* **SMTP Server Host**: `smtp.gmail.com`
* **SMTP Port**: `587`
* **Sender Email (SMTP User)**: `your-email@gmail.com` (Your actual Gmail address)
* **SMTP Password**: `abcdefghijklmnop` (The 16-character passcode, with spaces removed)
* **Internal Receiver Email**: `operations-team@company.com` (Where you want registration alerts to land)

---

## 🏢 Method 2: Microsoft Office 365 / Outlook

Office 365 requires SMTP AUTH to be active on the mailbox.

### Step 1: Enable SMTP Auth in Exchange Admin
*If you are using a standard free outlook.com email, skip this step. If using corporate Office 365:*
1. Log into your **Microsoft 365 Admin Center**.
2. Go to **Users** -> **Active Users** -> Click your email account.
3. Select the **Mail** tab -> Click **Manage email apps**.
4. Check the box for **Authenticated SMTP** and save changes.

### Step 2: Generate an App Password (If MFA is enabled)
1. Go to your **[Microsoft Additional Security Page](https://mysignins.microsoft.com/security-info)**.
2. Add a new sign-in method -> select **App password**.
3. Copy the unique **16-character passcode** provided.

### Step 3: Input Settings into Admin Dashboard
* **SMTP Server Host**: `smtp.office365.com`
* **SMTP Port**: `587`
* **Sender Email (SMTP User)**: `your-email@outlook.com` (or your company Office 365 email)
* **SMTP Password**: Your app password (or actual password if MFA is disabled)
* **Internal Receiver Email**: `operations-team@company.com`

---

## ⚡ Method 3: SendGrid (Best for Production Delivery)

SendGrid is built for automated bulk/transactional emails and avoids spam filters.

### Step 1: Create an API Key
1. Log into your **[SendGrid Dashboard](https://app.sendgrid.com/)**.
2. Navigate to **Settings** -> **API Keys**.
3. Click **Create API Key**.
4. Select **Full Access** and name the key (e.g., `AxeGlobal Portal`).
5. Copy the generated API Key starting with `SG....` *Note: This displays once!*

### Step 2: Verify Sender Identity
1. Go to **Settings** -> **Sender Authentication**.
2. Complete **Single Sender Verification** to approve the email address you want to send mail from.

### Step 3: Input Settings into Admin Dashboard
* **SMTP Server Host**: `smtp.sendgrid.net`
* **SMTP Port**: `587`
* **Sender Email (SMTP User)**: `apikey` (Strictly write the literal string `apikey`, not your account username!)
* **SMTP Password**: `SG.your_full_api_key_copied_in_step_1`
* **Internal Receiver Email**: `operations-team@company.com`

---

## 🧪 How to Verify Your Configurations

1. **Log in** to `http://127.0.0.1:5000/auth/login` as `admin@axeglobal.com` / `Admin@123!`.
2. Open the **Settings** panel (bottom-left) and input your chosen credentials, then click **Apply Configurations**.
3. **Verify Password Reset**:
   * Log out or open an Incognito tab.
   * Go to `http://127.0.0.1:5000/auth/forgot_password`.
   * Type in the email of any active user (e.g., `admin@axeglobal.com`) and click **Send Reset Link**.
   * Check the mailbox. A secure password reset link should land in your inbox within seconds!
4. **Verify Registration Request**:
   * On the login page, click **Request Access**.
   * Fill out the form as a new user.
   * Hit **Sign Up**.
   * Your configured **Internal Receiver Email** will instantly receive an automated email notifying them of the new registration!
