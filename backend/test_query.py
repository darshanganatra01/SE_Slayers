import os
from app import create_app, db
from app.models.customer_order_detail import CustomerOrderDetail

app = create_app()
with app.app_context():
    details = CustomerOrderDetail.query.limit(2).all()
    for d in details:
        print(f"Detail found: {d.codid}")
        
    if not details:
        print("No order details found in DB!")
    else:
        print("Trying to test CustomerItemDetail logic on:", details[0].codid)
        detail = details[0]
        sku = detail.sku
        order = detail.customer_order
        print("Order:", order, "SKU:", sku)
        
        from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
        from app.models.packing_slip import PackingSlip
        
        inv_details = CustomerInvDetail.query.join(CustomerInvoice).join(PackingSlip)\
            .filter(PackingSlip.coid == order.coid, CustomerInvDetail.skuid == detail.skuid)\
            .order_by(CustomerInvoice.invoice_date.asc()).all()
        print(f"Invoice details found: {len(inv_details)}")
        
        from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail
        try:
            received_details = DeliveryReceiptDetail.query.join(DeliveryReceipt).join(CustomerInvoice).join(PackingSlip)\
                .filter(PackingSlip.coid == order.coid, DeliveryReceiptDetail.skuid == detail.skuid)\
                .order_by(DeliveryReceipt.received_date.asc()).all()
            print(f"Received details found: {len(received_details)}")
        except Exception as e:
            print("ERROR in received_details query:", repr(e))
            
