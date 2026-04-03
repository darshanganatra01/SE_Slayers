import os
import sys

from app import create_app, db
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.customer import Customer

app = create_app()
with app.app_context():
    # Find a customer
    cust = Customer.query.first()
    if not cust:
        print("No customers found")
        exit()
    
    print(f"Testing for Customer CID: {cust.cid}")
    
    details = CustomerOrderDetail.query.join(CustomerOrderDetail.customer_order)\
        .filter(CustomerOrderDetail.customer_order.has(cid=cust.cid)).all()
    
    if not details:
        print("No items found for this customer")
        exit()
        
    d = details[0]
    print(f"List ID (detail.codid): {d.codid}")
    
    lookup = CustomerOrderDetail.query.filter_by(codid=d.codid).first()
    if lookup:
        print(f"  Successfully found item {d.codid} using .filter_by(codid=...)")
    else:
        print(f"  FAILED to find item {d.codid} using .filter_by(codid=...)")