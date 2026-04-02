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
            
        # Dummy invoice since subsystem not ready
        dummy_invoice = {
            "cInvId": f"INV-{order.coid}",
            "status": "Unpaid"
        }
            
        return {
            "order": {
                "coId": order.coid,
                "orderDate": order.order_date.isoformat() if order.order_date else "",
                "status": order.status or "Unknown"
            },
            "totalAmount": float(order.total_amount) if order.total_amount else 0.0,
            "invoice": dummy_invoice,
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
            return {"message": "Order placed successfully", "order_id": order_id}, 201
            
        except Exception as e:
            import traceback
            db.session.rollback()
            with open("error.log", "w") as f:
                f.write(traceback.format_exc())
            return {"message": f"An error occurred: {str(e)}"}, 500

