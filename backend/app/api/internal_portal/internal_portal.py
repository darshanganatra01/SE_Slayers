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
from app.models.payment import Payment
from app.models.order_board_ranking import (
    HighPriorityRanking, MediumPriorityRanking, LowPriorityRanking, RANKING_MODELS
)
from flask import request
import uuid
import re as re_mod
from datetime import date
from app.utils.email_utils import send_customer_shipment_email

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

def map_acp_to_priority(acp_int):
    """Map customer ACP category to order priority."""
    if acp_int is None:
        return "Medium"
    if acp_int <= 15:
        return "High"
    elif acp_int <= 30:
        return "Medium"
    else:
        return "Low"

from datetime import timedelta

@internal_ns.route("/overview")
class InternalOverviewResource(Resource):
    def get(self):
        # 1. Pending orders (not Completed)
        # Status map: Draft, Confirmed, Packed, PartiallyPacked, FullyPacked, PartiallyFulfilled -> Pending
        all_orders = db.session.query(CustomerOrder).all()
        pending_orders = 0
        high_priority = 0
        
        for o in all_orders:
            if o.status not in ["Completed", "Cancelled", "Dispatched"]:
                pending_orders += 1
                acp = o.customer.acp if o.customer and o.customer.acp else 30
                priority = o.priority or map_acp_to_priority(acp)
                if priority == "High":
                    high_priority += 1

        # 3. Low stock items
        all_skus = db.session.query(SA_SKU).all()
        low_stock_skus = []
        for s in all_skus:
            thr = s.threshold if s.threshold is not None else 10
            qty = s.stock_qty if s.stock_qty is not None else 0
            if qty < thr:
                low_stock_skus.append(s)
        
        low_stock_count = len(low_stock_skus)

        # 4. Quarterly revenue – based on shipped invoices, not payments collected
        three_months_ago = date.today() - timedelta(days=90)
        shipped_invoices = (
            db.session.query(CustomerInvoice)
            .join(PackingSlip, CustomerInvoice.pslip_id == PackingSlip.pslip_id)
            .filter(
                PackingSlip.status == "Shipped",
                CustomerInvoice.invoice_date >= three_months_ago,
            )
            .all()
        )
        quarterly_revenue = sum(float(inv.total_amount or 0) for inv in shipped_invoices)

        # 5. Overdue alert
        invoices = db.session.query(CustomerInvoice).all()
        overdue_amt = 0.0
        overdue_customers = set()
        longest_outstanding = 0
        today = date.today()

        for inv in invoices:
            total_amt = float(inv.total_amount or 0)
            paid_amt = sum(float(p.amount) for p in inv.payments.all())
            if paid_amt < total_amt and total_amt > 0:
                # Find ACP
                order = None
                if inv.packing_slip:
                    order = inv.packing_slip.customer_order
                
                acp = order.customer.acp if order and order.customer and order.customer.acp else 30
                
                days_outstanding = (today - inv.invoice_date).days
                if days_outstanding > acp:
                    overdue_amt += (total_amt - paid_amt)
                    if order and order.customer:
                        overdue_customers.add(order.customer.cid)
                    if days_outstanding > longest_outstanding:
                        longest_outstanding = days_outstanding

        # 6. Priority orders (top 5 pending by ACP)
        pending_orders_list = [o for o in all_orders if o.status not in ["Completed", "Cancelled"]]
        pending_orders_list.sort(key=lambda x: (x.customer.acp if x.customer and x.customer.acp else 30, x.order_date))
        
        priority_orders_dto = []
        for o in pending_orders_list[:5]:
            cname = o.customer.customer_name if o.customer else "Unknown"
            val = float(o.total_amount or 0)
            score = o.customer.acp if o.customer and o.customer.acp else 30
            priority_orders_dto.append({
                "id": o.coid,
                "name": cname,
                "placedOn": o.order_date.strftime("%B %d %Y") if o.order_date else "",
                "val": f"₹{val:,.0f}",
                "score": score
            })

        # 7. Low Stock List (top 5)
        low_stock_dto = []
        for s in low_stock_skus[:5]:
            pname = s.skuid
            # resolve pname via VendorProduct -> Product
            vp = db.session.query(VendorProduct).filter_by(vpid=s.vpid).first()
            if vp:
                p = db.session.query(Product).filter_by(pid=vp.pid).first()
                if p:
                    pname = p.pname
            
            low_stock_dto.append({
                "name": pname,
                "qty": s.stock_qty or 0,
                "max": s.threshold or 10
            })

        # 8. Activity Feed
        recent_orders = db.session.query(CustomerOrder).order_by(CustomerOrder.order_date.desc()).limit(3).all()
        recent_payments = db.session.query(Payment).order_by(Payment.payment_date.desc()).limit(3).all()
        recent_invoices = db.session.query(CustomerInvoice).order_by(CustomerInvoice.invoice_date.desc()).limit(3).all()

        activities = []
        for o in recent_orders:
            activities.append({
                "date": o.order_date,
                "color": "#2563eb",
                "title": "Order placed",
                "desc": f"{o.coid} · {o.customer.customer_name if o.customer else ''}",
                "amt": f"₹{o.total_amount or 0:,.0f}",
                "amtColor": "#09090b"
            })
        for p in recent_payments:
            inv_str = f"INV-{p.cinv_id.split('-')[-1]}" if p.cinv_id else "Payment"
            activities.append({
                "date": p.payment_date,
                "color": "#16a34a",
                "title": "Payment in",
                "desc": f"{inv_str} · {p.customer_invoice.packing_slip.customer_order.customer.customer_name if p.customer_invoice and p.customer_invoice.packing_slip and p.customer_invoice.packing_slip.customer_order else ''}",
                "amt": f"₹{p.amount:,.0f}",
                "amtColor": "#16a34a"
            })
        for i in recent_invoices:
            order = i.packing_slip.customer_order if i.packing_slip else None
            acp = order.customer.acp if order and order.customer and order.customer.acp else 30
            days_out = (today - i.invoice_date).days
            title = "Invoice raised"
            color = "#d97706"
            if days_out > acp:
                title = "Invoice overdue"
                color = "#dc2626"
            
            cname = order.customer.customer_name if order and order.customer else ""
            activities.append({
                "date": i.invoice_date,
                "color": color,
                "title": title,
                "desc": f"{i.cinv_id} · {cname}",
                "amt": f"₹{i.total_amount or 0:,.0f}",
                "amtColor": color if title == "Invoice overdue" else "#09090b"
            })

        activities.sort(key=lambda x: x["date"], reverse=True)
        time_labels = ["2m", "18m", "1h", "2h", "3h", "4h", "5h", "6h", "1d"]
        for idx, a in enumerate(activities):
            a["time"] = time_labels[idx] if idx < len(time_labels) else "1d"
            del a["date"]

        return {
            "metrics": {
                "pending": pending_orders,
                "highPriority": high_priority,
                "lowStock": low_stock_count,
                "quarterlyRevenue": quarterly_revenue
            },
            "overdue": {
                "amount": float(overdue_amt),
                "customers": len(overdue_customers),
                "longestOutstanding": longest_outstanding
            },
            "priorityOrders": priority_orders_dto,
            "activityFeed": activities[:6],
            "lowStockItems": low_stock_dto
        }, 200

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
            acp_val = customer.acp if customer and customer.acp is not None else 30
            priority = order.priority or map_acp_to_priority(acp_val)
            cust_type = map_cust_type(priority)
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
                    "customer": customer_name, "custType": cust_type, "priority": priority,
                    "value": f"₹{ip_value:,.2f}", "placedOn": date_str, "shop": shop_name, "items": ip_items,
                    "rank": 9999
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
                    "customer": customer_name, "custType": cust_type, "priority": priority,
                    "value": f"₹{p_value:,.2f}", "placedOn": date_str, "shop": shop_name, "items": p_items,
                    "pslip_ids": packing_slips_ids,
                    "rank": 9999
                })
                status_bucket_counts["packed"] += 1

            # --- BUCKET 3: SHIPPED ---
            s_items = []
            s_value = 0.0
            shipped_slips = [s for s in order.packing_slips if s.status == "Shipped"]
            cinv_ids = []
            all_received = True if shipped_slips else False
            
            for slip in shipped_slips:
                for inv in slip.invoices.all():
                    cinv_ids.append(inv.cinv_id)
                    if not inv.delivery_receipts.first():
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

            if s_items and not all_received:
                orders_data.append({
                    "id": f"{order.coid}-S", "status": "shipped", "order": status_bucket_counts["shipped"],
                    "customer": customer_name, "custType": cust_type, "priority": priority,
                    "value": f"₹{s_value:,.2f}", "placedOn": date_str, "shop": shop_name, "items": s_items,
                    "cinv_ids": cinv_ids,
                    "is_received": all_received,
                    "rank": 9999
                })
                status_bucket_counts["shipped"] += 1

        # ── Apply persisted rankings from the matching priority table ──
        for card in orders_data:
            card_id = card["id"]
            card_status = card["status"]
            card_priority = card["priority"]
            Model = RANKING_MODELS.get(card_priority)
            if Model:
                row = db.session.query(Model).filter_by(
                    coid=card_id, status=card_status
                ).first()
                if row is not None:
                    card["rank"] = row.rank

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
        
        # 0. Validate Stock Constraints First
        for ps_detail in slip.details:
            sku = db.session.query(SA_SKU).filter_by(skuid=ps_detail.skuid).first()
            if sku:
                unit_sell = sku.unit_measurement_sell or 1
                lot_sell = sku.lot_size_sell or 1
                actual_deduction = ps_detail.packed_qty * unit_sell * lot_sell
                stock_qty = sku.stock_qty or 0
                if stock_qty - actual_deduction < 0:
                    product_name = sku.skuid
                    vp = db.session.query(VendorProduct).filter_by(vpid=sku.vpid).first()
                    if vp:
                        product = db.session.query(Product).filter_by(pid=vp.pid).first()
                        if product:
                            product_name = product.pname
                    return {"message": f"Stock is not sufficient for {product_name}: {sku.skuid}"}, 400
        
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
        email_items = []
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
            
            if sku:
                unit_sell = sku.unit_measurement_sell or 1
                lot_sell = sku.lot_size_sell or 1
                actual_deduction = ps_detail.packed_qty * unit_sell * lot_sell
                sku.stock_qty = (sku.stock_qty or 0) - actual_deduction

            # Collect data for email notification
            product_name = ps_detail.skuid
            specs_str = ""
            if sku:
                vp = db.session.query(VendorProduct).filter_by(vpid=sku.vpid).first()
                if vp:
                    product = db.session.query(Product).filter_by(pid=vp.pid).first()
                    if product:
                        product_name = product.pname
                
                if sku.specs:
                    try:
                        import json
                        specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                        specs_str = " ".join([str(v) for v in specs_dict.values()]) if isinstance(specs_dict, dict) else str(sku.specs)
                    except:
                        specs_str = str(sku.specs)
            
            email_items.append({
                "name": product_name,
                "specs": specs_str,
                "qty": ps_detail.packed_qty,
                "price": sale_price,
                "amount": ps_detail.packed_qty * sale_price
            })
            
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
        
        # TRIGGER ASYNC THRESHOLD RECALCULATION
        import threading
        from flask import current_app
        from app.api.demand_forecast import update_all_sku_thresholds
        
        app_obj = current_app._get_current_object()
        threading.Thread(target=update_all_sku_thresholds, args=(app_obj,)).start()
        
        # TRIGGER ASYNC CUSTOMER SHIPMENT EMAIL
        customer_email = order.customer.email if order.customer else None
        if customer_email:
            threading.Thread(
                target=send_customer_shipment_email,
                args=(customer_email, cinv_id, email_items, total_inv_amount, order.coid)
            ).start()
        
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

def map_cust_type_to_acp(acp_int):
    if acp_int == 1: return "Platinum"
    if acp_int == 2: return "Gold"
    if acp_int == 3: return "Silver"
    return "Platinum"

@internal_ns.route("/customers")
class InternalCustomersResource(Resource):
    def get(self):
        customers = Customer.query.all()
        result = []
        
        for c in customers:
            total_orders = 0
            total_value = 0.0
            avg_pay_days = 0 
            
            c_data = {
                "id": c.cid,
                "name": c.customer_name,
                "biz": c.customer_name,
                "phone": c.contact or "",
                "email": c.email or "",
                "loc": c.location or "",
                "type": map_cust_type_to_acp(c.acp),
                "acp": c.acp if c.acp is not None else 30,
                "credit": 100000,
                "pending": 0,
                "totalOrders": 0,
                "totalValue": 0,
                "avgPayDays": 0,
                "invoices": [],
                "orders": [],
                "payHistory": []
            }
            
            orders = CustomerOrder.query.filter_by(cid=c.cid).all()
            orders.sort(key=lambda x: x.order_date)
            total_orders = len(orders)
            
            # ── Step 1: Build orders list (no pending/paid columns) ──
            all_invoices = []   # flat list of CustomerInvoice across all orders
            for o in orders:
                val = 0.0
                for d in o.details:
                    val += float(d.amount or 0)
                total_value += val
                
                # Collect invoices for this order
                for slip in o.packing_slips.all():
                    for inv in slip.invoices.all():
                        inv._assoc_order = o.coid
                        all_invoices.append(inv)
                
                c_data["orders"].append({
                    "id": o.coid,
                    "date": o.order_date.strftime("%b %d") if o.order_date else "",
                    "value": round(val, 2),
                    "status": o.status or "In-Process"
                })
            
            # ── Step 2: Gather ALL unique payments for this customer ──
            total_paid_customer = 0.0
            processed_customer_payments = set()
            
            for o in orders:
                # Direct payments to order
                for p in Payment.query.filter_by(coid=o.coid).all():
                    if p.payment_id not in processed_customer_payments:
                        total_paid_customer += float(p.amount)
                        processed_customer_payments.add(p.payment_id)
                        c_data["payHistory"].append({
                            "date": p.payment_date.strftime("%b %d") if p.payment_date else "",
                            "type": "payment",
                            "amount": float(p.amount),
                            "note": p.notes or f"Paid for {o.coid}"
                        })
                # Payments via invoices
                for slip in o.packing_slips.all():
                    for inv in slip.invoices.all():
                        for p in inv.payments.all():
                            if p.payment_id not in processed_customer_payments:
                                total_paid_customer += float(p.amount)
                                processed_customer_payments.add(p.payment_id)
                                c_data["payHistory"].append({
                                    "date": p.payment_date.strftime("%b %d") if p.payment_date else "",
                                    "type": "payment",
                                    "amount": float(p.amount),
                                    "note": p.notes or f"Paid for {inv.cinv_id}"
                                })

            # ── Step 3: Compute each invoice's effective paid amount ──
            # 1. Direct invoice payments (payments with cinv_id matching the invoice)
            # 2. Advance payments for the SAME order (coid matches, cinv_id is NULL)
            #    distributed FIFO across that order's invoices ONLY — advances
            #    for Order A must NOT bleed into Order B's invoices.
            all_invoices.sort(key=lambda x: x.invoice_date)
            
            # First, compute each invoice's directly-recorded paid amount
            inv_direct_paid = {}
            for inv in all_invoices:
                paid = sum(float(p.amount) for p in inv.payments.all())
                inv_direct_paid[inv.cinv_id] = paid
            
            # Group invoices by order for per-order advance distribution
            order_invoices = {}  # coid -> [invoice]
            for inv in all_invoices:
                coid = getattr(inv, '_assoc_order', '')
                order_invoices.setdefault(coid, []).append(inv)
            
            # For each order, compute its advance payments and distribute
            # FIFO across ONLY that order's invoices
            inv_effective_paid = {}
            for o in orders:
                # Compute advance payments for this order (coid set, cinv_id NULL)
                order_advance = 0.0
                for p in Payment.query.filter_by(coid=o.coid).all():
                    if not p.cinv_id:
                        order_advance += float(p.amount)
                
                # Distribute this order's advances across its invoices (oldest first)
                remaining_advance = order_advance
                for inv in order_invoices.get(o.coid, []):
                    inv_total = float(inv.total_amount or 0)
                    direct_paid = inv_direct_paid.get(inv.cinv_id, 0.0)
                    shortfall = max(0, inv_total - direct_paid)
                    
                    advance_alloc = 0.0
                    if remaining_advance > 0 and shortfall > 0:
                        advance_alloc = min(remaining_advance, shortfall)
                        remaining_advance -= advance_alloc
                    
                    inv_effective_paid[inv.cinv_id] = direct_paid + advance_alloc

            # ── Step 4: Build invoice DTOs with accurate status ──
            for inv in all_invoices:
                inv_total = float(inv.total_amount or 0)
                paid_amount = inv_effective_paid.get(inv.cinv_id, 0.0)
                
                status = "Paid" if (inv_total > 0 and round(paid_amount, 2) >= round(inv_total - 0.01, 2)) else "Unpaid"
                    
                c_data["invoices"].append({
                    "id": inv.cinv_id,
                    "desc": f"Order {getattr(inv, '_assoc_order', '')}",
                    "amount": round(inv_total, 2),
                    "paid_amount": round(paid_amount, 2),
                    "pending": round(max(0, inv_total - paid_amount), 2),
                    "date": inv.invoice_date.strftime("%b %d, %Y") if inv.invoice_date else "",
                    "status": status
                })
                
            # ── Step 5: Customer-level pending ──
            # Pending = sum of unpaid amounts across all invoices ONLY.
            # Orders that haven't been invoiced yet don't count as "pending"
            # because there's nothing to collect until an invoice is raised.
            pending = 0.0
            for inv in all_invoices:
                inv_total = float(inv.total_amount or 0)
                eff_paid = inv_effective_paid.get(inv.cinv_id, 0.0)
                if round(eff_paid, 2) < round(inv_total - 0.01, 2):
                    pending += (inv_total - eff_paid)
            c_data["pending"] = round(pending, 2)
            c_data["totalOrders"] = total_orders
            c_data["totalValue"] = round(total_value, 2)
            c_data["avgPayDays"] = avg_pay_days
            
            result.append(c_data)
            
        return result, 200

@internal_ns.route("/collect-payment")
class CollectPaymentResource(Resource):
    def post(self):
        data = request.json
        cid = data.get("cid")
        amount = float(data.get("amount", 0))
        
        if not cid or amount <= 0:
            return {"message": "Valid Customer ID and amount are required."}, 400
            
        customer = Customer.query.get(cid)
        if not customer:
            return {"message": "Customer not found."}, 404
            
        orders = CustomerOrder.query.filter_by(cid=cid).all()
        
        # ── Collect ALL invoices for this customer ──
        all_invoices = []
        for o in orders:
            for slip in o.packing_slips.all():
                for inv in slip.invoices.all():
                    inv._assoc_coid = o.coid
                    all_invoices.append(inv)
        
        # Sort FIFO: oldest invoice first
        all_invoices.sort(key=lambda x: x.invoice_date)
        
        # ── Compute inv_effective_paid (identical to GET endpoint) ──
        inv_direct_paid = {}
        for inv in all_invoices:
            paid = sum(float(p.amount) for p in inv.payments.all())
            inv_direct_paid[inv.cinv_id] = paid
            
        order_invoices = {}
        for inv in all_invoices:
            coid = getattr(inv, '_assoc_coid', '')
            order_invoices.setdefault(coid, []).append(inv)
            
        inv_effective_paid = {}
        for o in orders:
            order_advance = 0.0
            for p in Payment.query.filter_by(coid=o.coid).all():
                if not p.cinv_id:
                    order_advance += float(p.amount)
            
            remaining_advance = order_advance
            for inv in order_invoices.get(o.coid, []):
                inv_total = float(inv.total_amount or 0)
                direct_paid = inv_direct_paid.get(inv.cinv_id, 0.0)
                shortfall = max(0, inv_total - direct_paid)
                
                advance_alloc = 0.0
                if remaining_advance > 0 and shortfall > 0:
                    advance_alloc = min(remaining_advance, shortfall)
                    remaining_advance -= advance_alloc
                
                inv_effective_paid[inv.cinv_id] = direct_paid + advance_alloc

        # ── Find unpaid invoices ──
        unpaid_invoices = []
        total_pending = 0.0
        
        for inv in all_invoices:
            inv_total = float(inv.total_amount or 0)
            eff_paid = inv_effective_paid.get(inv.cinv_id, 0.0)
            
            if round(eff_paid, 2) < round(inv_total - 0.01, 2):
                inv_unpaid = inv_total - eff_paid
                unpaid_invoices.append({
                    "invoice": inv,
                    "unpaid": inv_unpaid,
                    "coid": inv._assoc_coid
                })
                total_pending += inv_unpaid
                
        if amount > round(total_pending, 2) + 0.01:
            return {"message": f"Amount (₹{amount:.2f}) exceeds total pending invoice amount (₹{total_pending:.2f})."}, 400
                
        rem_amount = amount
        payments_made = []
        
        from app.models.user import User
        active_user = User.query.first()
        uid = active_user.uid if active_user else "admin"

        import uuid
        from datetime import date
        
        for ui in unpaid_invoices:
            if rem_amount <= 0:
                break
                
            inv = ui["invoice"]
            inv_unpaid = ui["unpaid"]
            pay_amt = min(rem_amount, inv_unpaid)
            
            new_payment = Payment(
                payment_id="PAY-" + uuid.uuid4().hex[:6].upper(),
                coid=ui["coid"],
                cinv_id=inv.cinv_id,
                recorded_by=uid,
                payment_date=date.today(),
                amount=pay_amt,
                method="Auto-FIFO",
                notes=f"FIFO Collection (Invoice {inv.cinv_id})"
            )
            db.session.add(new_payment)
            
            payments_made.append({"invoice_id": inv.cinv_id, "order_id": ui["coid"], "amount": pay_amt})
            rem_amount -= pay_amt
            
        db.session.commit()
        return {
            "message": "Payment collected successfully", 
            "collected": amount - rem_amount, 
            "allocations": payments_made
        }, 200

@internal_ns.route("/new-order-data")
class NewOrderDataResource(Resource):
    def get(self):
        """Return all customers and products for the new order form."""
        customers = Customer.query.all()
        cust_list = []
        for c in customers:
            cust_list.append({
                "cid": c.cid,
                "customer_name": c.customer_name,
                "location": c.location or "",
                "acp": c.acp if c.acp is not None else 2,
                "priority": map_acp_to_priority(c.acp)
            })

        products = Product.query.all()
        prod_list = []
        for p in products:
            prod_list.append({
                "pid": p.pid,
                "pname": p.pname,
                "category": p.category or ""
            })

        return {"customers": cust_list, "products": prod_list}, 200


@internal_ns.route("/product-skus/<string:pid>")
class ProductSKUsResource(Resource):
    def get(self, pid):
        """Return all SKU variants for a given product."""
        import json as _json
        skus = (
            SA_SKU.query.join(VendorProduct)
            .filter(VendorProduct.pid == pid, SA_SKU.current_sell_rate.isnot(None))
            .all()
        )
        sku_list = []
        for s in skus:
            specs_str = ""
            if s.specs:
                try:
                    specs_dict = _json.loads(s.specs) if isinstance(s.specs, str) else s.specs
                    specs_str = " ".join([str(v) for v in specs_dict.values()])
                except Exception:
                    specs_str = str(s.specs)

            sku_list.append({
                "skuid": s.skuid,
                "specs": specs_str,
                "sell_rate": float(s.current_sell_rate) if s.current_sell_rate else 0.0,
                "stock_qty": s.stock_qty or 0
            })
        return sku_list, 200


@internal_ns.route("/create-order")
class CreateOrderResource(Resource):
    def post(self):
        """Create a new customer order with line items."""
        try:
            data = request.get_json()
            cid = data.get("cid")
            items = data.get("items", [])

            if not cid or not items:
                return {"message": "Customer and at least one item required"}, 400

            customer = Customer.query.get(cid)
            if not customer:
                return {"message": "Customer not found"}, 404

            priority = map_acp_to_priority(customer.acp)

            order_id = "CO-" + uuid.uuid4().hex[:8].upper()
            new_order = CustomerOrder(
                coid=order_id,
                cid=cid,
                created_by=customer.uid,
                order_date=date.today(),
                status="Confirmed",
                priority=priority,
                total_amount=0.0
            )
            db.session.add(new_order)

            total_amount = 0.0
            for item in items:
                sku_id = item.get("skuid")
                qty = int(item.get("quantity", 0))
                if qty <= 0:
                    continue

                sku = SA_SKU.query.get(sku_id)
                if not sku:
                    return {"message": f"SKU {sku_id} not found"}, 404

                sell_rate = float(sku.current_sell_rate) if sku.current_sell_rate else 0.0
                amount = qty * sell_rate
                total_amount += amount

                detail_id = "COD-" + uuid.uuid4().hex[:8].upper()
                detail = CustomerOrderDetail(
                    codid=detail_id,
                    coid=order_id,
                    skuid=sku_id,
                    quantity=qty,
                    amount=amount
                )
                db.session.add(detail)

            new_order.total_amount = total_amount
            db.session.commit()

            # TRIGGER ASYNC THRESHOLD RECALCULATION
            import threading
            from flask import current_app
            from app.api.demand_forecast import update_all_sku_thresholds
            
            app_obj = current_app._get_current_object()
            threading.Thread(target=update_all_sku_thresholds, args=(app_obj,)).start()

            return {"message": "Order created", "order_id": order_id, "total": round(total_amount, 2)}, 201

        except Exception as e:
            db.session.rollback()
            return {"message": f"Error: {str(e)}"}, 500

@internal_ns.route("/reorder-cards")
class ReorderCardsResource(Resource):
    def post(self):
        """Persist vertical reorder within a single priority column."""
        data = request.json
        status = data.get("status")          # "inprocess" / "packed"
        priority = data.get("priority")      # "High" / "Medium" / "Low"
        ordered_coids = data.get("ordered_coids", [])

        if not status or not priority or not ordered_coids:
            return {"message": "status, priority, and ordered_coids are required"}, 400

        if priority not in RANKING_MODELS:
            return {"message": f"Invalid priority: {priority}"}, 400

        Model = RANKING_MODELS[priority]

        try:
            for rank, coid in enumerate(ordered_coids):
                row = db.session.query(Model).filter_by(
                    coid=coid, status=status
                ).first()
                if row:
                    row.rank = rank
                else:
                    db.session.add(Model(coid=coid, status=status, rank=rank))

            db.session.commit()
            return {"message": "Reordered successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error: {str(e)}"}, 500


@internal_ns.route("/cross-drag")
class CrossDragResource(Resource):
    def post(self):
        """Move a card between priority columns and re-rank both columns."""
        data = request.json
        coid = data.get("coid")
        status = data.get("status")                # "inprocess" / "packed"
        from_priority = data.get("from_priority")   # "High" / "Medium" / "Low"
        to_priority = data.get("to_priority")
        to_rank = data.get("to_rank", 0)

        if not all([coid, status, from_priority, to_priority]):
            return {"message": "coid, status, from_priority, to_priority required"}, 400

        if from_priority not in RANKING_MODELS or to_priority not in RANKING_MODELS:
            return {"message": "Invalid priority value"}, 400

        SrcModel = RANKING_MODELS[from_priority]
        DstModel = RANKING_MODELS[to_priority]

        try:
            # 1. Find and remove from source table
            src_row = db.session.query(SrcModel).filter_by(
                coid=coid, status=status
            ).first()
            old_rank = src_row.rank if src_row else -1

            if src_row:
                db.session.delete(src_row)
                db.session.flush()

                # Re-rank source column: decrement ranks above the removed position
                remaining = db.session.query(SrcModel).filter(
                    SrcModel.status == status,
                    SrcModel.rank > old_rank
                ).all()
                for r in remaining:
                    r.rank -= 1

            # 2. Make room in destination column at to_rank
            shift = db.session.query(DstModel).filter(
                DstModel.status == status,
                DstModel.rank >= to_rank
            ).all()
            for r in shift:
                r.rank += 1

            # 3. Insert into destination table
            db.session.add(DstModel(coid=coid, status=status, rank=to_rank))

            # 4. Update actual order priority (strip -P / -S suffix)
            real_coid = re_mod.sub(r'-(P|S)$', '', coid)
            order = db.session.query(CustomerOrder).filter_by(coid=real_coid).first()
            if order:
                order.priority = to_priority

            db.session.commit()
            return {"message": "Cross-drag successful"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error: {str(e)}"}, 500
