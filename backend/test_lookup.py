from app import create_app, db
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.customer import Customer

app = create_app()
with app.app_context():
    cust = Customer.query.first()
    if not cust:
        print('No customers found')
    else:
        print(f'Testing for Customer CID: {cust.cid}')
        
        details = CustomerOrderDetail.query.join(CustomerOrderDetail.customer_order).filter(CustomerOrderDetail.customer_order.has(cid=cust.cid)).all()
        
        if not details:
            print('No items found for this customer')
        else:
            for d in details[:3]:
                print(f'List ID (detail.codid): {d.codid}')
                lookup = CustomerOrderDetail.query.get(d.codid)
                if lookup:
                    print(f'  Found using .get(): {lookup.codid}')
                else:
                    print(f'  FAILED using .get()')
                    
                lookup_filter = CustomerOrderDetail.query.filter_by(codid=d.codid).first()
                if lookup_filter:
                    print(f'  Found using filter_by: {lookup_filter.codid}')
                else:
                    print(f'  FAILED using filter_by')