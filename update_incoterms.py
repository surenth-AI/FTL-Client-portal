from app import create_app, db
from app.models.models import Lookup

app = create_app()

with app.app_context():
    existing_dpu = Lookup.query.filter_by(category='incoterm', code='DPU').first()
    if not existing_dpu:
        db.session.add(Lookup(category='incoterm', code='DPU', name='DPU - Delivered at Place Unloaded'))
        
    existing_exw = Lookup.query.filter_by(category='incoterm', code='EXW').first()
    if not existing_exw:
        db.session.add(Lookup(category='incoterm', code='EXW', name='EXW - Ex Works'))
        
    db.session.commit()
    print("Incoterms DPU and EXW successfully added to the database.")
