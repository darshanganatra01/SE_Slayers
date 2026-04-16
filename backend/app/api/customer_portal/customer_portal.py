from flask_restx import Namespace, Resource
from flask import request
from app import db
from app.models.product import Product
from app.models.sku import SKU
from app.models.vendor import VendorProduct
import json

customer_ns = Namespace('customer', description='Customer Portal operations')

@customer_ns.route('/test')
class CustomerTest(Resource):
    def get(self):
        return {"status": "Customer Portal is active"}

@customer_ns.route('/products')
class ProductList(Resource):
    def get(self):
        """Fetch all distinct products available for sale"""
        # Join Product -> VendorProduct -> SKU to only get products that have at least one SKU.
        # But for mock frontend parity, we return products directly.
        products = Product.query.all()
        results = []
        for p in products:
            # Get the first SKU to determine the unit measurement and min price
            first_sku = SKU.query.join(VendorProduct).filter(VendorProduct.pid == p.pid).first()
            unit_measurement = "piece"
            starting_price = 0.0
            
            if first_sku:
                unit = first_sku.unit_measurement_sell or 1
                if unit == 1:
                    unit_measurement = "piece"
                else:
                    unit_measurement = f"pack ({unit} pcs)"
                    
                # get all SKUs for minimum price
                product_skus = SKU.query.join(VendorProduct).filter(VendorProduct.pid == p.pid).all()
                if product_skus:
                    prices = [float(s.current_sell_rate) for s in product_skus if s.current_sell_rate is not None]
                    if prices:
                        starting_price = min(prices)
            
            # Use mock image logic
            image = f"@/customer_dashboard/customer_assets/{p.pname}.png".replace("G. I.", "GI")
            
            results.append({
                "pid": p.pid,
                "pName": p.pname,
                "category": p.category,
                "unitMeasurement": unit_measurement,
                "image": image,
                "startingPrice": starting_price
            })
        
        return results, 200


@customer_ns.route('/categories')
class ProductCategoryList(Resource):
    def get(self):
        """Fetch all unique product categories"""
        categories = db.session.query(Product.category).distinct().all()
        # categories is a list of tuples: [('Plumbing',), ('Hardware',), (None,)]
        result = [c[0] for c in categories if c[0] and c[0].strip()]
        return sorted(result), 200



@customer_ns.route('/products/<string:pid>')
class ProductDetail(Resource):
    def get(self, pid):
        """Fetch a specific product and its SKUs"""
        p = Product.query.get(pid)
        if not p:
            return {"message": "Product not found"}, 404
            
        first_sku = SKU.query.join(VendorProduct).filter(VendorProduct.pid == p.pid).first()
        unit_measurement = "piece"
        if first_sku:
            unit = first_sku.unit_measurement_sell or 1
            if unit == 1:
                unit_measurement = "piece"
            else:
                unit_measurement = f"pack ({unit} pcs)"

        image = f"@/customer_dashboard/customer_assets/{p.pname}.png".replace("G. I.", "GI")
        
        product_data = {
            "pid": p.pid,
            "pName": p.pname,
            "category": p.category,
            "unitMeasurement": unit_measurement,
            "image": image
        }
        
        # Get all SKUs for this product
        skus = SKU.query.join(VendorProduct).filter(VendorProduct.pid == p.pid).all()
        sku_list = []
        for sku in skus:
            # Format specs into a single string
            specs_str = ""
            if sku.specs:
                try:
                    specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                    specs_str = " ".join([str(v) for v in specs_dict.values()])
                except Exception:
                    specs_str = str(sku.specs)
            
            sku_list.append({
                "skuId": sku.skuid,
                "vpId": sku.vpid,
                "pid": p.pid,
                "currentBuy": float(sku.current_buy_rate) if sku.current_buy_rate else 0.0,
                "currentSell": float(sku.current_sell_rate) if sku.current_sell_rate else 0.0,
                "specs": specs_str,
                "stockQty": sku.stock_qty or 0
            })
            
        return {
            "product": product_data,
            "skus": sku_list
        }, 200

import uuid
from datetime import datetime
from app.models.customer_order import CustomerOrder
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.customer import Customer
from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
from app.models.packing_slip import PackingSlip

@customer_ns.route('/invoices')
class CustomerInvoices(Resource):
    def get(self):
        """Fetch all invoices for a specific customer"""
        cid = request.args.get('cid')
        if not cid:
            return {"message": "Customer ID is required"}, 400
            
        # Join CustomerInvoice -> PackingSlip -> CustomerOrder
        invoices = CustomerInvoice.query.join(PackingSlip).join(CustomerOrder)\
            .filter(CustomerOrder.cid == cid)\
            .order_by(CustomerInvoice.invoice_date.desc()).all()
            
        results = []
        for inv in invoices:
            # Get first 3 unique product names
            items = []
            unique_products = []
            for detail in inv.details.all():
                sku = detail.sku
                p_name = sku.vendor_product.product.pname if sku and sku.vendor_product and sku.vendor_product.product else "Unknown"
                if p_name not in unique_products:
                    unique_products.append(p_name)
                
                if len(unique_products) <= 3:
                    items.append(p_name)
            
            items_str = ", ".join(unique_products[:3])
            if len(unique_products) > 3:
                items_str += "..."
                
            receipt = inv.delivery_receipts.first()
            results.append({
                "cInvId": inv.cinv_id,
                "coId": inv.packing_slip.coid,
                "invoiceDate": inv.invoice_date.isoformat() if inv.invoice_date else "",
                "totalAmount": float(inv.total_amount) if inv.total_amount else 0.0,
                "status": inv.status or "Unpaid",
                "itemsSummary": items_str,
                "isReceived": receipt is not None
            })
            
        return results, 200

@customer_ns.route('/invoices/<string:invId>')
class CustomerInvoiceDetail(Resource):
    def get(self, invId):
        """Fetch details for a specific invoice"""
        inv = CustomerInvoice.query.get(invId)
        if not inv:
            return {"message": "Invoice not found"}, 404
            
        items = []
        for detail in inv.details.all():
            sku = detail.sku
            product = sku.vendor_product.product if sku and sku.vendor_product else None
            
            specs_str = ""
            if sku and sku.specs:
                try:
                    specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                    specs_str = " ".join([str(v) for v in specs_dict.values()])
                except Exception:
                    specs_str = str(sku.specs)
            
            items.append({
                "cDetailId": detail.cdetail_id,
                "orderedQty": detail.ordered_qty or 0,
                "deliveredQty": detail.delivered_qty or 0,
                "salePrice": float(detail.sale_price) if detail.sale_price else 0.0,
                "amount": float(detail.amount) if detail.amount else 0.0,
                "sku": {
                    "skuId": sku.skuid if sku else "Unknown",
                    "specs": specs_str
                },
                "product": {
                    "pName": product.pname if product else "Unknown Product"
                }
            })
            
        receipt = inv.delivery_receipts.first()
        receipt_info = None
        if receipt:
            receipt_info = {
                "receiptId": receipt.receipt_id,
                "receivedDate": receipt.received_date.isoformat(),
                "notes": receipt.notes,
                "receivedBy": receipt.receiver.full_name if receipt.receiver else "Unknown"
            }

        return {
            "invoice": {
                "cInvId": inv.cinv_id,
                "invoiceDate": inv.invoice_date.isoformat() if inv.invoice_date else "",
                "status": inv.status or "Unpaid",
                "totalAmount": float(inv.total_amount) if inv.total_amount else 0.0,
                "coId": inv.packing_slip.coid if inv.packing_slip else "",
                "receipt": receipt_info
            },
            "items": items
        }, 200


@customer_ns.route('/orders/<string:coId>')
class CustomerOrderDetailResource(Resource):
    def get(self, coId):
        """Fetch details for a specific order"""
        order = CustomerOrder.query.get(coId)
        if not order:
            return {"message": "Order not found"}, 404
            
        items = []
        for detail in order.details.all():
            sku = detail.sku
            product = sku.vendor_product.product if sku.vendor_product else None
            
            # Format specs string
            specs_str = ""
            if sku.specs:
                try:
                    specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                    specs_str = " ".join([str(v) for v in specs_dict.values()])
                except Exception:
                    specs_str = str(sku.specs)
                    
            # Calculate sale price derived from amount and quantity
            qty = detail.quantity or 1
            sale_price = float(detail.amount) / qty if detail.amount else 0.0
                    
            items.append({
                "cDetailId": detail.codid,
                "orderedQty": qty,
                "deliveredQty": 0, # Hardcoded 0 or derived from status
                "salePrice": sale_price,
                "sku": {
                    "skuId": sku.skuid,
                    "specs": specs_str
                },
                "product": {
                    "pName": product.pname if product else "Unknown Product"
                }
            })
            
        # Get real invoices associated with this order via PackingSlips
        invoices = CustomerInvoice.query.join(PackingSlip).filter(PackingSlip.coid == coId).all()
        invoice_list = []
        total_delivered_by_sku = {}
        
        for inv in invoices:
            invoice_list.append({
                "cInvId": inv.cinv_id,
                "status": inv.status or "Unpaid",
                "invoiceDate": inv.invoice_date.isoformat() if inv.invoice_date else ""
            })
            # Track delivered quantities per SKU
            for inv_detail in inv.details:
                sku_id = inv_detail.skuid
                delivered = inv_detail.delivered_qty or 0
                total_delivered_by_sku[sku_id] = total_delivered_by_sku.get(sku_id, 0) + delivered

        # Update items with real delivered quantities
        for item in items:
            sku_id = item["sku"]["skuId"]
            item["deliveredQty"] = total_delivered_by_sku.get(sku_id, 0)
            
        return {
            "order": {
                "coId": order.coid,
                "orderDate": order.order_date.isoformat() if order.order_date else "",
                "status": order.status or "Unknown"
            },
            "totalAmount": float(order.total_amount) if order.total_amount else 0.0,
            "invoices": invoice_list,
            "items": items
        }, 200


@customer_ns.route('/orders')
class CustomerOrders(Resource):
    def get(self):
        """Fetch all orders for a specific customer"""
        cid = request.args.get('cid')
        if not cid:
            return {"message": "Customer ID is required"}, 400
            
        orders = CustomerOrder.query.filter_by(cid=cid).order_by(CustomerOrder.order_date.desc()).all()
        results = []
        
        for order in orders:
            items = []
            # details relationship is lazy="dynamic"
            for detail in order.details.all():
                sku = detail.sku
                product = sku.vendor_product.product if sku.vendor_product else None
                
                # Format specs string reusing logic
                specs_str = ""
                if sku.specs:
                    try:
                        specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                        specs_str = " ".join([str(v) for v in specs_dict.values()])
                    except Exception:
                        specs_str = str(sku.specs)
                        
                items.append({
                    "quantity": detail.quantity,
                    "sku": {
                        "skuId": sku.skuid,
                        "specs": specs_str
                    },
                    "product": {
                        "pName": product.pname if product else "Unknown Product"
                    }
                })
                
            results.append({
                "order": {
                    "coId": order.coid,
                    "orderDate": order.order_date.isoformat() if order.order_date else "",
                    "status": order.status or "Unknown"
                },
                "totalAmount": float(order.total_amount) if order.total_amount else 0.0,
                "items": items
            })
            
        return results, 200

    def post(self):
        """Place a new order"""
        try:
            data = request.json
            cid = data.get('cid')
            items = data.get('items', [])
            
            if not cid or not items:
                return {"message": "Customer ID and items are required"}, 400
                
            customer = Customer.query.get(cid)
            if not customer:
                return {"message": "Customer not found"}, 404
                
            # Create Order
            import uuid
            from datetime import datetime
            
            order_id = "CO-" + uuid.uuid4().hex[:8].upper()
            new_order = CustomerOrder(
                coid=order_id,
                cid=cid,
                created_by=customer.uid,
                order_date=datetime.utcnow().date(),
                status="Confirmed",
                priority="Medium",  # Hardcoded for now per instructions
                total_amount=0.0
            )
            
            db.session.add(new_order)
            total_order_amount = 0.0
            
            for item in items:
                sku_id = item.get('skuId')
                qty = int(item.get('quantity', 0))
                
                if qty <= 0:
                    continue
                    
                sku = SKU.query.get(sku_id)
                if not sku:
                    continue
                    
                # amount calculation
                sell_rate = float(sku.current_sell_rate) if sku.current_sell_rate else 0.0
                amount = qty * sell_rate
                total_order_amount += amount
                
                # Stock subtraction logic removed per requirements (stock only reduced on shipping)
                # unit_sell = sku.unit_measurement_sell or 1
                # lot_sell = sku.lot_size_sell or 1
                # subtract_qty = qty * unit_sell * lot_sell
                # if sku.stock_qty is not None:
                #     sku.stock_qty -= subtract_qty
                    
                # Create Order Detail
                detail_id = "COD-" + uuid.uuid4().hex[:8].upper()
                order_detail = CustomerOrderDetail(
                    codid=detail_id,
                    coid=order_id,
                    skuid=sku_id,
                    quantity=qty,
                    amount=amount
                )
                db.session.add(order_detail)
                
            new_order.total_amount = total_order_amount
            db.session.commit()
            
            # TRIGGER ASYNC THRESHOLD RECALCULATION
            import threading
            from flask import current_app
            from app.api.demand_forecast import update_all_sku_thresholds
            
            app_obj = current_app._get_current_object()
            threading.Thread(target=update_all_sku_thresholds, args=(app_obj,)).start()
            
            return {"message": "Order placed successfully", "order_id": order_id}, 201
            
        except Exception as e:
            import traceback
            db.session.rollback()
            with open("error.log", "w") as f:
                f.write(traceback.format_exc())
            return {"message": f"An error occurred: {str(e)}"}, 500


@customer_ns.route('/items')
class CustomerItems(Resource):
    def get(self):
        """Fetch all individual items ordered by a customer"""
        cid = request.args.get('cid')
        if not cid:
            return {"message": "Customer ID is required"}, 400
            
        # Join CustomerOrderDetail -> CustomerOrder
        details = CustomerOrderDetail.query.join(CustomerOrder)\
            .filter(CustomerOrder.cid == cid)\
            .order_by(CustomerOrder.order_date.desc()).all()
            
        results = []
        for detail in details:
            sku = detail.sku
            product = sku.vendor_product.product if sku and sku.vendor_product else None
            order = detail.customer_order
            
            # Determine status
            # Find any invoice details for this SKU belonging to invoices of this order
            invoiced_qty = db.session.query(db.func.sum(CustomerInvDetail.delivered_qty))\
                .join(CustomerInvoice).join(PackingSlip)\
                .filter(PackingSlip.coid == order.coid, CustomerInvDetail.skuid == detail.skuid)\
                .scalar() or 0
                
            status = "Shipped" if invoiced_qty > 0 else "Confirmed"
            
            # Format specs
            specs_str = ""
            if sku and sku.specs:
                try:
                    specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                    specs_str = " ".join([str(v) for v in specs_dict.values()])
                except Exception:
                    specs_str = str(sku.specs)
            
            results.append({
                "codId": detail.codid,
                "coId": order.coid,
                "pName": product.pname if product else "Unknown",
                "specs": specs_str,
                "quantity": detail.quantity,
                "status": status,
                "orderDate": order.order_date.isoformat() if order.order_date else ""
            })
            
        return results, 200

@customer_ns.route('/items/<string:codId>')
class CustomerItemDetail(Resource):
    def get(self, codId):
        """Fetch timeline and details for a specific ordered item"""
        detail = CustomerOrderDetail.query.filter_by(codid=codId).first()
        if not detail:
            return {"message": "Item not found"}, 404
            
        sku = detail.sku
        product = sku.vendor_product.product if sku and sku.vendor_product else None
        order = detail.customer_order
        
        # Get shipping and receiving info
        inv_details = CustomerInvDetail.query.join(CustomerInvoice).join(PackingSlip)\
            .filter(PackingSlip.coid == order.coid, CustomerInvDetail.skuid == detail.skuid)\
            .order_by(CustomerInvoice.invoice_date.asc()).all()
            
        timeline = [
            {"status": "Confirmed", "date": order.order_date.isoformat() if order.order_date else "", "completed": True, "qty": detail.quantity or 0}
        ]
        
        has_shipped = False
        for inv_det in inv_details:
            qty = inv_det.delivered_qty or 0
            if qty > 0:
                has_shipped = True
                date_str = inv_det.customer_invoice.invoice_date.isoformat() if inv_det.customer_invoice and inv_det.customer_invoice.invoice_date else ""
                timeline.append({"status": "Shipped", "date": date_str, "completed": True, "qty": qty})
                
        if not has_shipped:
            timeline.append({"status": "Shipped", "date": "", "completed": False, "qty": 0})

        # Get received info
        from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail
        received_details = DeliveryReceiptDetail.query.join(DeliveryReceipt).join(CustomerInvoice).join(PackingSlip)\
            .filter(PackingSlip.coid == order.coid, DeliveryReceiptDetail.skuid == detail.skuid)\
            .order_by(DeliveryReceipt.received_date.asc()).all()
            
        has_received = False
        for rec_det in received_details:
            qty = rec_det.received_qty or 0
            if qty > 0:
                has_received = True
                date_str = rec_det.delivery_receipt.received_date.isoformat() if rec_det.delivery_receipt and rec_det.delivery_receipt.received_date else ""
                timeline.append({"status": "Received", "date": date_str, "completed": True, "qty": qty})
                
        if not has_received:
            timeline.append({"status": "Received", "date": "", "completed": False, "qty": 0})
        
        # Format specs
        specs_str = ""
        if sku and sku.specs:
            try:
                specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                specs_str = " ".join([str(v) for v in specs_dict.values()])
            except Exception:
                specs_str = str(sku.specs)

        return {
            "codId": detail.codid,
            "coId": order.coid,
            "product": {
                "pName": product.pname if product else "Unknown",
                "specs": specs_str
            },
            "quantity": detail.quantity,
            "amount": float(detail.amount) if detail.amount else 0.0,
            "timeline": timeline
        }, 200


@customer_ns.route('/receive')
class CustomerReceiveResource(Resource):
    def post(self):
        """Confirm receipt of an invoice"""
        from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail
        data = request.json
        cinv_id = data.get('cinv_id')
        uid = data.get('uid')
        notes = data.get('notes', '')
        items_data = data.get('items') # Optional list of {skuid, received_qty, condition}
        
        if not cinv_id or not uid:
            return {"message": "Invoice ID and User ID are required"}, 400
            
        invoice = CustomerInvoice.query.get(cinv_id)
        if not invoice:
            return {"message": "Invoice not found"}, 404
            
        # Check if already received
        existing_receipt = DeliveryReceipt.query.filter_by(cinv_id=cinv_id).first()
        if existing_receipt:
            return {"message": "Receipt already confirmed for this invoice"}, 400
            
        receipt_id = "DR-" + uuid.uuid4().hex[:8].upper()
        new_receipt = DeliveryReceipt(
            receipt_id=receipt_id,
            cinv_id=cinv_id,
            received_by=uid,
            received_date=datetime.utcnow().date(),
            notes=notes
        )
        db.session.add(new_receipt)
        
        if items_data:
            for item in items_data:
                skuid = item.get('skuid')
                received_qty = int(item.get('received_qty', 0))
                condition = item.get('condition', 'Good')
                
                drd_id = "DRD-" + uuid.uuid4().hex[:8].upper()
                detail = DeliveryReceiptDetail(
                    dr_detail_id=drd_id,
                    receipt_id=receipt_id,
                    skuid=skuid,
                    received_qty=received_qty,
                    condition=condition
                )
                db.session.add(detail)
        else:
            # Default: Receive all items in the invoice
            for inv_detail in invoice.details:
                drd_id = "DRD-" + uuid.uuid4().hex[:8].upper()
                detail = DeliveryReceiptDetail(
                    dr_detail_id=drd_id,
                    receipt_id=receipt_id,
                    skuid=inv_detail.skuid,
                    received_qty=inv_detail.delivered_qty or 0,
                    condition='Good'
                )
                db.session.add(detail)
                
        db.session.commit()
        return {"message": "Receipt confirmed successfully", "receipt_id": receipt_id}, 201
