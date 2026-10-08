import sys
from app import create_app, db
app = create_app()
with app.app_context():
    try:
        from sqlalchemy import text
        db.session.execute(text('ALTER TABLE system_setting ADD smtp_sender_name VARCHAR(255)'))
        db.session.commit()
        print('Column added successfully')
    except Exception as e:
        print('Error:', e)
