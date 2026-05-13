import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'freight-portal-secret-2025-xk9p'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'axeglobal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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
