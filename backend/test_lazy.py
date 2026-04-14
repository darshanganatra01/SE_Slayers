from app import app, db
from app.models.customer import Customer
from app.models.customer_order import CustomerOrder

with app.app_context():
    c = Customer.query.first()
    orders = CustomerOrder.query.filter_by(cid=c.cid).all()
    for o in orders:
        invoices = []
        # Try both
        slips1 = list(o.packing_slips)
        slips2 = o.packing_slips.all()
        print(f"Order: {o.coid}, slips list: {len(slips1)}, slips all: {len(slips2)}")
        
        for slip in o.packing_slips:
            for inv in slip.invoices.all():
                print(f"  Invoice: {inv.cinv_id}, total: {inv.total_amount}")
