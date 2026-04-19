import csv
import uuid
import sys
import os
from datetime import datetime
from decimal import Decimal

# Ensure python path allows importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.customer import Customer
from app.models.user import User
from app.models.customer_order import CustomerOrder
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.packing_slip import PackingSlip, PackingSlipDetail
from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail

from dotenv import load_dotenv

def main():
    load_dotenv()
    print("Initializing Flask App Context...")
    app = create_app()
    with app.app_context():
        print("Finding customer seslayer@gmail.com...")
        # Find the customer
        email = "seslayer@gmail.com"
        customer = Customer.query.filter_by(email=email).first()
        if not customer:
            user = User.query.filter_by(email=email).first()
            if user:
                customer = Customer.query.filter_by(uid=user.uid).first()
        
        if not customer:
            print(f"Error: Could not find customer with email {email}")
            sys.exit(1)
            
        print(f"Found customer: {customer.cid} / {customer.customer_name}")
        
        # Read the CSV data
        csv_path = os.path.join(os.path.dirname(__file__), 'fake_order_data.csv')
        orders_data = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                coid = row['coid'].strip()
                if coid not in orders_data:
                    orders_data[coid] = {
                        'order_date': row['order_date'].strip(),
                        'items': []
                    }
                orders_data[coid]['items'].append({
                    'codid': row['codid'].strip(),
                    'skuid': row['skuid'].strip(),
                    'quantity': int(row['quantity']),
                    'amount': Decimal(row['amount']),
                })

        # Process each order
        for coid, data in orders_data.items():
            order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()
            
            # Check if order already exists
            existing_order = CustomerOrder.query.filter_by(coid=coid).first()
            if existing_order:
                print(f"Order {coid} already exists. Skipping.")
                continue
                
            total_amount = sum(item['amount'] for item in data['items'])
            
            # 1. Create Customer Order
            new_order = CustomerOrder(
                coid=coid,
                cid=customer.cid,
                created_by=customer.uid,
                order_date=order_date,
                status="Completed",
                priority="Medium",
                total_amount=total_amount
            )
            db.session.add(new_order)
            
            for item in data['items']:
                order_detail = CustomerOrderDetail(
                    codid=item['codid'],
                    coid=coid,
                    skuid=item['skuid'],
                    quantity=item['quantity'],
                    amount=item['amount']
                )
                db.session.add(order_detail)
            
            # 2. Create Packing Slip
            pslip_id = "PS-" + uuid.uuid4().hex[:8].upper()
            new_slip = PackingSlip(
                pslip_id=pslip_id,
                coid=coid,
                packed_by=customer.uid,
                packed_date=order_date,
                status="Shipped"
            )
            db.session.add(new_slip)
            
            for item in data['items']:
                psd_id = "PSD-" + uuid.uuid4().hex[:8].upper()
                packing_detail = PackingSlipDetail(
                    psd_id=psd_id,
                    pslip_id=pslip_id,
                    skuid=item['skuid'],
                    packed_qty=item['quantity']
                )
                db.session.add(packing_detail)
                
            # 3. Create Customer Invoice
            cinv_id = "INV-" + uuid.uuid4().hex[:8].upper()
            new_invoice = CustomerInvoice(
                cinv_id=cinv_id,
                pslip_id=pslip_id,
                created_by=customer.uid,
                invoice_date=order_date,
                status="Paid",
                total_amount=total_amount
            )
            db.session.add(new_invoice)
            
            for item in data['items']:
                cdetail_id = "CD-" + uuid.uuid4().hex[:8].upper()
                sale_price = item['amount'] / item['quantity'] if item['quantity'] > 0 else Decimal('0')
                invoice_detail = CustomerInvDetail(
                    cdetail_id=cdetail_id,
                    cinv_id=cinv_id,
                    skuid=item['skuid'],
                    ordered_qty=item['quantity'],
                    delivered_qty=item['quantity'],
                    sale_price=sale_price,
                    amount=item['amount']
                )
                db.session.add(invoice_detail)
                
            # 4. Create Delivery Receipt
            receipt_id = "DR-" + uuid.uuid4().hex[:8].upper()
            new_receipt = DeliveryReceipt(
                receipt_id=receipt_id,
                cinv_id=cinv_id,
                received_by=customer.uid,
                received_date=order_date,
                notes="Auto-received from fake order seeding"
            )
            db.session.add(new_receipt)
            
            for item in data['items']:
                dr_detail_id = "DRD-" + uuid.uuid4().hex[:8].upper()
                receipt_detail = DeliveryReceiptDetail(
                    dr_detail_id=dr_detail_id,
                    receipt_id=receipt_id,
                    skuid=item['skuid'],
                    received_qty=item['quantity'],
                    condition="Good"
                )
                db.session.add(receipt_detail)
                
        # Commit all transactions
        db.session.commit()
        print(f"Successfully seeded {len(orders_data)} orders!")

if __name__ == '__main__':
    main()
