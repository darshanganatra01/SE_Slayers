import os
from app import create_app, db

# Make sure models are registered
from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail

app = create_app()
with app.app_context():
    print("Creating any missing database tables...")
    db.create_all()
    print("Done!")
