from app import db, create_app
from app.models.customer import Customer
import os

app = create_app()
with app.app_context():
    cust = Customer.query.filter_by(uid='USR-CUST01').first()
    if cust:
        print(f"CID: {cust.cid}")
    else:
        print("Customer USR-CUST01 not found")
        all_custs = Customer.query.all()
        for c in all_custs:
            print(f"UID: {c.uid}, CID: {c.cid}")
