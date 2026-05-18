import os
import urllib
from dotenv import load_dotenv

# Load local environment variables from .env file if present
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
        
        if driver == '{SQL Server}':
            # Legacy {SQL Server} driver requires a simpler string without modern parameters
            odbc_str = (
                f"Driver={driver};"
                f"Server={server},1433;"
                f"Database={database};"
                f"Uid={username};"
                f"Pwd={password};"
            )
        else:
            # Modern drivers (ODBC 17/18) use security features
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
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'use_setinputsizes': False}
    }
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

    # Company Branding & Legal Details
    COMPANY_DETAILS = {
        'name': 'AxeGlobal Logistics GmbH',
        'address': 'Logistics Center, Port Road 42, 20457 Hamburg, Germany',
        'vat_id': 'DE 123 456 789',
        'email': 'billing@axeglobal-logistics.com',
        'website': 'www.axeglobal-logistics.com',
        'bank_name': 'AXEGLOBAL Global Settlement Bank',
        'iban': 'DE99 1234 5678 9012 3456 78',
        'swift': 'AXEGLOBALXXHH',
        'footer_text': 'All business is transacted subject to the ADSp conditions. Thank you for choosing AXEGLOBAL.'
    }
