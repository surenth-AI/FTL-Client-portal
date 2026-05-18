# 🌐 Step-by-Step Guide: Setting Up Azure SQL Database & Connecting Flask

This guide will walk you through provisioning an Azure SQL Database, configuring security firewalls, extracting the correct connection string, setting up local dependencies, updating your Flask configurations, and initializing your tables.

---

## 📋 Table of Contents
1. [Step 1: Create an Azure SQL Database in the Azure Portal](#step-1-create-an-azure-sql-database-in-the-azure-portal)
2. [Step 2: Configure Firewall Security (Crucial)](#step-2-configure-firewall-security-crucial)
3. [Step 3: Extract the ODBC Connection String](#step-3-extract-the-odbc-connection-string)
4. [Step 4: Prepare the Local Python Environment](#step-4-prepare-the-local-python-environment)
5. [Step 5: Update the Flask Configurations (`config.py`)](#step-5-update-the-flask-configurations-configpy)
6. [Step 6: Initialize Database Tables & Seed Data](#step-6-initialize-database-tables--seed-data)

---

## 🚀 Step 1: Create an Azure SQL Database in the Azure Portal

1. **Log In to the Azure Portal**:
   - Go to [portal.azure.com](https://portal.azure.com) and log in with your credentials.

2. **Navigate to SQL Databases**:
   - Search for **SQL databases** in the top search bar and click on it.
   - Click the **+ Create** or **Create SQL database** button.

3. **Configure Project Details**:
   - **Subscription**: Select your active Azure subscription.
   - **Resource Group**: Select an existing one or click *Create new* (e.g., `axeglobal-rg`).

4. **Configure Database Details**:
   - **Database Name**: Enter a name (e.g., `axeglobal-db`).
   - **Server**: Click **Create new** just below the dropdown.
     - **Server Name**: Enter a globally unique name (e.g., `axeglobal-sql-server`).
     - **Location**: Choose a region close to you or your application host (e.g., `East US` or `West Europe`).
     - **Authentication Method**: Select **Use SQL authentication** (simplest for standard connections).
     - **Server Admin Login**: Enter an admin username (e.g., `axeadmin`).
     - **Password**: Create and save a strong password (you will need this for the connection string).
     - Click **OK**.

5. **Configure Compute + Storage (Save Costs!)**:
   - By default, Azure might select a costly production tier.
   - Under **Compute + storage**, click **Configure database**.
   - Change the **Service tier** from *General Purpose (Serverless)* to **Basic** or **Standard (S0)** (e.g., S0 DTU pricing model or Basic is extremely inexpensive, around $5–$15/month, perfect for development).
   - Click **Apply**.

6. **Review and Create**:
   - Skip to the **Review + create** tab at the bottom.
   - Click **Create**. It will take 1–3 minutes to deploy the SQL Server and Database resources.

---

## 🔒 Step 2: Configure Firewall Security (Crucial)

By default, Azure SQL Server blocks *all* external traffic. You must explicitly whitelist your local computer's IP address.

1. Once the deployment is complete, click **Go to resource** to open your SQL Database.
2. In the top toolbar, click **Set server firewall**.
3. Under **Public network access**, ensure it is set to **Selected networks**.
4. In the **Firewall rules** section:
   - Click **+ Add your client IPv4 address** (this auto-detects and adds your local machine's external IP).
   - *Optional:* To allow your app to connect when eventually deployed to Azure App Service, toggle **Allow Azure services and resources to access this server** to **Yes**.
5. Click **Save** at the bottom.

---

## 🔑 Step 3: Extract the ODBC Connection String

1. Go back to your SQL Database overview page.
2. In the left-hand sidebar under **Settings**, click on **Connection strings**.
3. Select the **ODBC** tab.
4. Copy the connection string. It will look like this:
   ```text
   Driver={ODBC Driver 18 for SQL Server};Server=tcp:axeglobal-sql-server.database.windows.net,1433;Database=axeglobal-db;Uid={your_username};Pwd={your_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
   ```
   > [!IMPORTANT]
   > Replace `{your_username}` with your administrator login (e.g., `axeadmin`) and `{your_password}` with your SQL server password.
   > If you receive SSL verification errors locally, you can change `TrustServerCertificate=no` to `TrustServerCertificate=yes`.

---

## 🐍 Step 4: Prepare the Local Python Environment

To connect Python Flask/SQLAlchemy to Microsoft SQL Server, you must install the standard `pyodbc` driver:

1. **Install python-dotenv & pyodbc**:
   Open a terminal in your workspace and run:
   ```bash
   pip install pyodbc python-dotenv
   ```
   *(Note: Ensure you have Microsoft ODBC Driver installed on your Windows machine, which is usually pre-installed. If not, download it from Microsoft's website).*

2. **Create a `.env` File**:
   In the root directory of your workspace (`d:\FTL-DEV\`), create a new file named `.env` and insert your credentials:
   ```env
   # .env
   SECRET_KEY=freight-portal-secret-2025-xk9p
   
   # Individual DB credentials (Option A)
   DB_SERVER=axeglobal-sql-server.database.windows.net
   DB_NAME=axeglobal-db
   DB_USER=axeadmin
   DB_PASSWORD=your_secure_password_here
   DB_DRIVER={ODBC Driver 18 for SQL Server}
   
   # OR direct ODBC Connection String (Option B)
   # AZURE_SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:axeglobal-sql-server.database.windows.net,1433;Database=axeglobal-db;Uid=axeadmin;Pwd=your_secure_password_here;Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;
   ```

---

## 🛠️ Step 5: Update the Flask Configurations (`config.py`)

We will update the `config.py` file to automatically check for environment variables and build the SQL Server connection string using `urllib` to properly handle special characters in your password.

Here is the updated configuration block that we will write to [config.py](file:///d:/FTL-DEV/config.py):

```python
import os
import urllib
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'freight-portal-secret-2025-xk9p'
    
    # -------------------------------------------------------------
    # Dynamic Database Connection Resolver (Azure SQL vs SQLite)
    # -------------------------------------------------------------
    azure_conn_str = os.environ.get('AZURE_SQL_CONNECTION_STRING')
    db_server = os.environ.get('DB_SERVER')
    
    if azure_conn_str:
        # Wrap the raw ODBC string inside SQLAlchemy's query format
        if not azure_conn_str.startswith('mssql+pyodbc://'):
            params = urllib.parse.quote_plus(azure_conn_str)
            SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
        else:
            SQLALCHEMY_DATABASE_URI = azure_conn_str
            
    elif db_server:
        # Construct raw ODBC string dynamically from separated environment variables
        server = db_server
        database = os.environ.get('DB_NAME')
        username = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        driver = os.environ.get('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')
        
        odbc_str = (
            f"Driver={driver};"
            f"Server=tcp:{server},1433;"
            f"Database={database};"
            f"Uid={username};"
            f"Pwd={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"  # Highly recommended locally to bypass SSL validation
            f"Connection Timeout=30;"
        )
        params = urllib.parse.quote_plus(odbc_str)
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
    else:
        # Fallback to local SQLite database if no Azure settings are defined
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'axeglobal.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ... (rest of configuration)
```

---

## 🏗️ Step 6: Initialize Database Tables & Seed Data

Since the application uses `db.create_all()` inside [app/\_\_init\_\_.py](file:///d:/FTL-DEV/app/__init__.py), **simply launching the Flask app will automatically detect your Azure SQL Server and generate all 18+ tables, indexes, and primary keys for you!**

To trigger this, execute in your terminal:
```powershell
python app.py
```

### 💡 Verifying Your Setup
Once the server runs, you will see a message:
`Admin user created: admin@axeglobal.com / admin123`

This confirms:
1. The app connected successfully to your remote Azure SQL Server.
2. The schema and tables were fully provisioned.
3. The default administrator account was seeded into your Azure database.

You can verify the tables using any SQL client (like Azure Data Studio, SSMS, or VS Code SQL Server extension) by connecting with your server name, database name, username, and password!
