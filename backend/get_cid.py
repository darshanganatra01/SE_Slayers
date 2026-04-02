from app import create_app, db
from app.models.customer import Customer
app = create_app()
with app.app_context():
    cust = Customer.query.first()
    print("CID:", cust.cid if cust else "None")
