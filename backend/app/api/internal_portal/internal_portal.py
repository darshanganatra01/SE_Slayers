from flask_restx import Namespace, Resource
from flask import jsonify
from app import db
from app.models.customer_order import CustomerOrder
from app.models.customer import Customer
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.sku import SKU as SA_SKU
from app.models.vendor import VendorProduct
from app.models.product import Product
from app.models.packing_slip import PackingSlip, PackingSlipDetail
from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
from flask import request
import uuid
from datetime import date

internal_ns = Namespace("internal-portal", description="Internal Portal operations")


def map_status(db_status):
    if db_status in ["Draft", "Confirmed"]:
        return "inprocess"
    elif db_status in ["Packed", "PartiallyPacked", "FullyPacked"]:
        return "packed"
    elif db_status in ["Dispatched", "PartiallyFulfilled", "Completed"]:
        return "shipped"
    return "inprocess"

def map_cust_type(priority):
    if priority == "High":
        return "VIP"
    elif priority == "Low":
        return "Delayed"
    return "Regular"

@internal_ns.route("/orders")
class InternalOrdersResource(Resource):
    def get(self):
        # We need to build the orders array and the inventory dictionary.
        orders_data = []
        inventory_data = {}
        
        # 1. Fetch Orders
        orders = db.session.query(CustomerOrder).all()
        
        status_bucket_counts = {"inprocess": 0, "packed": 0, "shipped": 0}

        for order in orders:
            customer = order.customer
            customer_name = customer.customer_name if customer else "Unknown"
            shop_name = customer.company_name if hasattr(customer, "company_name") else customer_name
            cust_type = map_cust_type(order.priority)
            date_str = order.order_date.strftime("%B %d %Y") if order.order_date else ""

            # Fetch all details and calculate distribution
            details = db.session.query(CustomerOrderDetail).filter_by(coid=order.coid).all()
            
            # Map items and inventory
            all_items_info = {}
            for detail in details:
                sku = db.session.query(SA_SKU).filter_by(skuid=detail.skuid).first()
                display_name = detail.skuid
                item_key = detail.skuid
                specs_str = ""
                stock = 0
                if sku:
                    vp = db.session.query(VendorProduct).filter_by(vpid=sku.vpid).first()
                    if vp:
                        product = db.session.query(Product).filter_by(pid=vp.pid).first()
                        if product:
                            display_name = product.pname
                            item_key = f"{product.pname} (ID: {sku.skuid})"
                    
                    stock = sku.stock_qty if sku.stock_qty else 0
                    if sku.specs:
                        import json
                        specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                        specs_str = " ".join([str(v) for v in specs_dict.values()]) if isinstance(specs_dict, dict) else str(sku.specs)
                    
                    inventory_data[item_key] = {"stock": stock, "max": sku.threshold or 20}

                # Calculate unit price from detail.amount / detail.quantity
                # If quantity is 0 (shouldn't happen), use 0
                unit_price = float(detail.amount / detail.quantity) if detail.quantity and detail.quantity > 0 else 0.0

                all_items_info[detail.skuid] = {
                    "name": display_name,
                    "skuid": detail.skuid,
                    "specs": specs_str,
                    "total_ordered": detail.quantity or 0,
                    "stock": stock,
                    "unit_price": unit_price
                }

            # Calculate packed/shipped quantities per SKU from slips
            packed_in_slips = {}   # SKU -> qty (status="Packed")
            shipped_in_slips = {}  # SKU -> qty (status="Shipped")
            total_processed = {}   # SKU -> qty (Packed + Shipped)

            for slip in order.packing_slips:
                for psd in slip.details:
                    if slip.status == "Packed":
                        packed_in_slips[psd.skuid] = packed_in_slips.get(psd.skuid, 0) + psd.packed_qty
                    else:
                        shipped_in_slips[psd.skuid] = shipped_in_slips.get(psd.skuid, 0) + psd.packed_qty
                    total_processed[psd.skuid] = total_processed.get(psd.skuid, 0) + psd.packed_qty

            # --- BUCKET 1: IN PROGRESS (Remaining to be packed) ---
            ip_items = []
            ip_value = 0.0
            for skuid, info in all_items_info.items():
                rem = info["total_ordered"] - total_processed.get(skuid, 0)
                if rem > 0:
                    ip_items.append({
                        "name": info["name"], "skuid": skuid, "specs": info["specs"],
                        "qty": rem, "packed_qty": 0, "inStock": info["stock"] > 0
                    })
                    ip_value += (rem * info["unit_price"])
            if ip_items:
                orders_data.append({
                    "id": order.coid, "status": "inprocess", "order": status_bucket_counts["inprocess"],
                    "customer": customer_name, "custType": cust_type, "priority": order.priority or "Medium",
                    "value": f"₹{ip_value:,.2f}", "placedOn": date_str, "shop": shop_name, "items": ip_items
                })
                status_bucket_counts["inprocess"] += 1

            # --- BUCKET 2: PACKED (Not yet shipped) ---
            p_items = []
            p_value = 0.0
            for skuid, qty in packed_in_slips.items():
                if qty > 0:
                    info = all_items_info.get(skuid, {"name": skuid, "specs": "", "unit_price": 0.0})
                    p_items.append({
                        "name": info["name"], "skuid": skuid, "specs": info.get("specs", ""),
                        "qty": qty, "packed_qty": qty, "inStock": True
                    })
                    p_value += (qty * info["unit_price"])
            if p_items:
                # Include packing slips IDs for backend actions like ship/unpack
                packing_slips_ids = [s.pslip_id for s in order.packing_slips if s.status == "Packed"]
                orders_data.append({
                    "id": f"{order.coid}-P", "status": "packed", "order": status_bucket_counts["packed"],
                    "customer": customer_name, "custType": cust_type, "priority": order.priority or "Medium",
                    "value": f"₹{p_value:,.2f}", "placedOn": date_str, "shop": shop_name, "items": p_items,
                    "pslip_ids": packing_slips_ids
                })
                status_bucket_counts["packed"] += 1

            # --- BUCKET 3: SHIPPED ---
            s_items = []
            s_value = 0.0
            shipped_slips = [s for s in order.packing_slips if s.status == "Shipped"]
            cinv_ids = []
            all_received = True if shipped_slips else False
            
            for slip in shipped_slips:
                if slip.customer_invoice:
                    cinv_ids.append(slip.customer_invoice.cinv_id)
                    if not slip.customer_invoice.delivery_receipts.first():
                        all_received = False
                        
                for psd in slip.details:
                    info = all_items_info.get(psd.skuid, {"name": psd.skuid, "specs": "", "unit_price": 0.0})
                    # Find if this item already in s_items
                    existing = next((x for x in s_items if x["skuid"] == psd.skuid), None)
                    if existing:
                        existing["qty"] += psd.packed_qty
                        existing["packed_qty"] += psd.packed_qty
                    else:
                        s_items.append({
                            "name": info["name"], "skuid": psd.skuid, "specs": info.get("specs", ""),
                            "qty": psd.packed_qty, "packed_qty": psd.packed_qty, "inStock": True
                        })
                    s_value += (psd.packed_qty * info["unit_price"])

            if s_items:
                orders_data.append({
                    "id": f"{order.coid}-S", "status": "shipped", "order": status_bucket_counts["shipped"],
                    "customer": customer_name, "custType": cust_type, "priority": order.priority or "Medium",
                    "value": f"₹{s_value:,.2f}", "placedOn": date_str, "shop": shop_name, "items": s_items,
                    "cinv_ids": cinv_ids,
                    "is_received": all_received
                })
                status_bucket_counts["shipped"] += 1

        return {"orders": orders_data, "inventory": inventory_data}, 200

@internal_ns.route("/pack")
class InternalPackResource(Resource):
    def post(self):
        data = request.json
        coid = data.get("coid")
        items = data.get("items", []) # List of {skuid, packed_qty}
        
        if not coid:
            return {"message": "Order ID is required"}, 400
        
        # Strip status suffixes (-P, -S, etc) added for the UI split
        import re
        coid = re.sub(r'-(P|S|PACKED|SHIPPED)$', '', coid)
        
        order = db.session.query(CustomerOrder).filter_by(coid=coid).first()
        if not order:
            return {"message": f"Order {coid} not found"}, 404
        
        # 1. Validate Quantities
        # Sum ordered quantities by SKU (handles multiple lines for same SKU)
        order_details = db.session.query(CustomerOrderDetail).filter_by(coid=coid).all()
        ordered_qty = {}
        for d in order_details:
            ordered_qty[d.skuid] = ordered_qty.get(d.skuid, 0) + (d.quantity or 0)

        # First, find what's already packed
        already_packed = {}
        past_slips = db.session.query(PackingSlip).filter_by(coid=coid).all()
        for slip in past_slips:
            for detail in slip.details:
                already_packed[detail.skuid] = already_packed.get(detail.skuid, 0) + detail.packed_qty
        
        for item in items:
            skuid = item.get("skuid")
            packed_qty = item.get("packed_qty", 0)
            if packed_qty <= 0: continue
            
            total_after = already_packed.get(skuid, 0) + packed_qty
            if total_after > ordered_qty.get(skuid, 0):
                return {"message": f"Packed quantity for {skuid} exceeds ordered quantity ({ordered_qty.get(skuid, 0)})."}, 400
            
        # 2. Create Packing Slip
        pslip_id = f"PS-{uuid.uuid4().hex[:6].upper()}"
        new_slip = PackingSlip(
            pslip_id=pslip_id,
            coid=coid,
            packed_by=order.created_by, # For now, assuming creator. Ideally, should be the logged-in user.
            packed_date=date.today(),
            status="Packed"
        )
        db.session.add(new_slip)
        
        for item in items:
            skuid = item.get("skuid")
            packed_qty = item.get("packed_qty", 0)
            if packed_qty <= 0: continue
            
            psd_id = f"PSD-{uuid.uuid4().hex[:6].upper()}"
            detail = PackingSlipDetail(
                psd_id=psd_id,
                pslip_id=pslip_id,
                skuid=skuid,
                packed_qty=packed_qty
            )
            db.session.add(detail)
            
            # Update running total for status check
            already_packed[skuid] = already_packed.get(skuid, 0) + packed_qty
            
        # 3. Update Order Status
        total_ordered = sum(ordered_qty.values())
        total_packed = sum(already_packed.values())
        
        if total_packed >= total_ordered:
            order.status = "FullyPacked"
        elif total_packed > 0:
            order.status = "PartiallyPacked"
            
        db.session.commit()
        
        return {
            "message": "Packed successfully",
            "pslip_id": pslip_id,
            "status": order.status
        }, 200

@internal_ns.route("/unpack")
class InternalUnpackResource(Resource):
    def post(self):
        data = request.json
        pslip_id = data.get("pslip_id")
        
        if not pslip_id:
            return {"message": "Packing Slip ID is required"}, 400
        
        slip = db.session.query(PackingSlip).filter_by(pslip_id=pslip_id).first()
        if not slip:
            return {"message": f"Packing Slip {pslip_id} not found"}, 404
        
        if slip.status == "Shipped":
            return {"message": "Cannot unpack a shipped batch"}, 400
        
        coid = slip.coid
        # Delete details first
        db.session.query(PackingSlipDetail).filter_by(pslip_id=pslip_id).delete()
        # Delete slip
        db.session.delete(slip)
        
        # Recalculate order status
        order = db.session.query(CustomerOrder).filter_by(coid=coid).first()
        if order:
            remaining_slips = db.session.query(PackingSlip).filter_by(coid=coid).count()
            if remaining_slips == 0:
                order.status = "Confirmed"
            else:
                order.status = "PartiallyPacked"
        
        db.session.commit()
        return {"message": "Unpacked successfully"}, 200

@internal_ns.route("/ship")
class InternalShipResource(Resource):
    def post(self):
        data = request.json
        pslip_id = data.get("pslip_id")
        
        if not pslip_id:
            return {"message": "Packing Slip ID is required"}, 400
            
        slip = db.session.query(PackingSlip).filter_by(pslip_id=pslip_id).first()
        if not slip:
            return {"message": f"Packing Slip {pslip_id} not found"}, 404
            
        if slip.status == "Shipped":
            return {"message": "Already shipped"}, 400
            
        order = db.session.query(CustomerOrder).filter_by(coid=slip.coid).first()
        
        # 1. Create Invoice
        cinv_id = f"INV-{uuid.uuid4().hex[:6].upper()}"
        invoice = CustomerInvoice(
            cinv_id=cinv_id,
            pslip_id=pslip_id,
            created_by=order.created_by,
            invoice_date=date.today(),
            status="Unpaid",
            total_amount=0
        )
        db.session.add(invoice)
        
        total_inv_amount = 0
        for ps_detail in slip.details:
            sku = db.session.query(SA_SKU).filter_by(skuid=ps_detail.skuid).first()
            sale_price = sku.current_sell_rate if sku and sku.current_sell_rate else 0
            
            # Find original ordered quantity
            orig_detail = db.session.query(CustomerOrderDetail).filter_by(coid=slip.coid, skuid=ps_detail.skuid).first()
            ordered_qty = orig_detail.quantity if orig_detail else ps_detail.packed_qty
            
            cdetail_id = f"CD-{uuid.uuid4().hex[:6].upper()}"
            inv_detail = CustomerInvDetail(
                cdetail_id=cdetail_id,
                cinv_id=cinv_id,
                skuid=ps_detail.skuid,
                ordered_qty=ordered_qty,
                delivered_qty=ps_detail.packed_qty,
                sale_price=sale_price,
                amount=ps_detail.packed_qty * sale_price
            )
            db.session.add(inv_detail)
            total_inv_amount += (ps_detail.packed_qty * sale_price)
            
        invoice.total_amount = total_inv_amount
        
        # 2. Update Packing Slip Status
        slip.status = "Shipped"
        
        # 3. Update Order Status
        # Calculate total ordered vs total delivered across ALL invoices for this order
        order_details = db.session.query(CustomerOrderDetail).filter_by(coid=slip.coid).all()
        total_ordered = sum(d.quantity for d in order_details)
        
        # Sum of delivered_qty from all invoices for this order's packing slips
        all_invoices = db.session.query(CustomerInvoice).join(PackingSlip).filter(PackingSlip.coid == slip.coid).all()
        total_delivered = 0
        for inv in all_invoices:
            for d in inv.details:
                total_delivered += d.delivered_qty
        # Don't forget current invoice details (manual as they are pending commit or we just calculated)
        # Actually since I added to session, I can just recalculate
        
        if total_delivered >= total_ordered:
            order.status = "Completed"
        else:
            order.status = "PartiallyFulfilled"
            
        db.session.commit()
        return {
            "message": "Shipped successfully",
            "cinv_id": cinv_id,
            "status": order.status
        }, 200
@internal_ns.route("/receive")
class InternalMarkReceivedResource(Resource):
    def post(self):
        """Admin backdoor: confirm receipt on behalf of customer"""
        from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail
        data = request.json
        cinv_id = data.get('cinv_id')
        uid = data.get('uid') # Admin UID
        
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
            received_date=date.today(),
            notes="Marked as received by Admin"
        )
        db.session.add(new_receipt)
        
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
        return {"message": "Receipt confirmed successfully by Admin", "receipt_id": receipt_id}, 201
