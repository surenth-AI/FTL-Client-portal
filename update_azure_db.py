import os
from dotenv import load_dotenv

# We load dotenv first so we can override it if we want, 
# but actually we will just set DB_SERVER manually
load_dotenv()
os.environ['DB_SERVER'] = 'ftl.database.windows.net'

# Now import the app to ensure config uses the DB_SERVER
from app import create_app, db
from app.models.models import User, UserBranchMapping

app = create_app()

with app.app_context():
    user = User.query.filter_by(email='customer@demo.com').first()
    if user:
        # Check if they already have branch_id 23
        existing = UserBranchMapping.query.filter_by(user_id=user.id, branch_id='23').first()
        if not existing:
            branch_mapping = UserBranchMapping(user_id=user.id, branch_id='23')
            db.session.add(branch_mapping)
            db.session.commit()
            print(f"Successfully mapped Branch ID 23 to {user.email} in Azure DB!")
        else:
            print(f"User {user.email} already has Branch ID 23 in Azure DB.")
    else:
        print("User customer@demo.com not found in Azure DB!")
