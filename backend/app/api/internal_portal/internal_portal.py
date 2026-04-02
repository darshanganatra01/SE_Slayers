from flask_restx import Namespace, Resource
from flask import jsonify
from app import db
from app.models.customer_order import CustomerOrder
from app.models.customer import Customer
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.sku import SKU
from app.models.vendor import VendorProduct
from app.models.product import Product

internal_ns = Namespace("internal-portal", description="Internal Portal operations")


def map_status(db_status):
    if db_status in ["Draft", "Confirmed"]:
        return "inprocess"
    elif db_status == "Packed":
        return "packed"
    elif db_status == "Dispatched":
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
        
        status_counts = {"inprocess": 0, "packed": 0, "shipped": 0}

        for order in orders:
            status_mapped = map_status(order.status)
            
            customer = order.customer
            customer_name = customer.customer_name if customer else "Unknown"
            shop_name = customer.company_name if hasattr(customer, "company_name") else customer_name
            cust_type = map_cust_type(order.priority)
            
            # Format value
            value_str = f"₹{order.total_amount:,.2f}" if order.total_amount else "₹0.00"
            date_str = order.order_date.strftime("%B %d %Y") if order.order_date else ""

            order_payload = {
                "id": order.coid,
                "status": status_mapped,
                "order": status_counts[status_mapped],
                "customer": customer_name,
                "custType": cust_type,
                "priority": order.priority or "Medium",
                "value": value_str,
                "placedOn": date_str,
                "shop": shop_name,
                "items": []
            }
            
            status_counts[status_mapped] += 1
            
            # 2. Fetch Details for the order
            details = db.session.query(CustomerOrderDetail).filter_by(coid=order.coid).all()
            for detail in details:
                sku = db.session.query(SKU).filter_by(skuid=detail.skuid).first()
                item_name = detail.skuid
                in_stock = False
                specs_str = ""
                if sku:
                    vp = db.session.query(VendorProduct).filter_by(vpid=sku.vpid).first()
                    if vp:
                        product = db.session.query(Product).filter_by(pid=vp.pid).first()
                        if product:
                            item_name = f"{product.pname} ({sku.skuid})"
                    
                    stock = sku.stock_qty if sku.stock_qty else 0
                    in_stock = stock > 0
                    
                    # Resolve specs
                    if sku.specs:
                        import json
                        specs_dict = json.loads(sku.specs) if isinstance(sku.specs, str) else sku.specs
                        if isinstance(specs_dict, dict):
                            specs_str = " · ".join([f"{k}: {v}" for k, v in specs_dict.items()])
                        else:
                            specs_str = str(sku.specs)
                    
                    inventory_data[item_name] = {
                        "stock": stock,
                        "max": sku.threshold if sku.threshold else 20
                    }
                
                order_payload["items"].append({
                    "name": item_name,
                    "specs": specs_str,
                    "inStock": in_stock,
                    "qty": detail.quantity or 1
                })

            orders_data.append(order_payload)

        return {"orders": orders_data, "inventory": inventory_data}, 200
