import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app import db
from app.models.customer import Customer
from app.models.customer_invoice import CustomerInvDetail, CustomerInvoice
from app.models.customer_order import CustomerOrder
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail
from app.models.packing_slip import PackingSlip
from app.models.product import Product
from app.models.sku import SKU
from app.models.user import User
from app.models.vendor import Vendor, VendorProduct


def test_customer_portal_test_route(client):
    response = client.get("/api/customer/test")
    assert response.status_code == 200
    assert response.get_json()["status"] == "Customer Portal is active"


def test_product_list_returns_products_with_details(client, app):
    with app.app_context():
        # Setup Data
        v = Vendor(vid="V1", vendor_name="Vendor 1", vendor_prefix="V1")
        p = Product(pid="P1", pname="G. I. Pipe", category="Pipes")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku1 = SKU(
            skuid="S1",
            vpid="VP1",
            unit_measurement_sell=10,
            current_sell_rate=Decimal("15.50"),
        )
        sku2 = SKU(
            skuid="S2",
            vpid="VP1",
            unit_measurement_sell=1,
            current_sell_rate=Decimal("12.00"),
        )
        
        p2 = Product(pid="P2", pname="Valve", category="Valves")
        vp2 = VendorProduct(vpid="VP2", vid="V1", pid="P2")
        sku3 = SKU(
            skuid="S3",
            vpid="VP2",
            unit_measurement_sell=1,
            current_sell_rate=Decimal("50.00"),
        )

        # Standalone product without SKUs
        p3 = Product(pid="P3", pname="Empty Product", category="Misc")

        db.session.add_all([v, p, vp, sku1, sku2, p2, vp2, sku3, p3])
        db.session.commit()

    response = client.get("/api/customer/products")
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 3

    # G. I. Pipe (unit_measurement = 10 -> pack (10 pcs), min price 12.0)
    p1_data = next(d for d in data if d["pid"] == "P1")
    assert p1_data["pName"] == "G. I. Pipe"
    assert p1_data["category"] == "Pipes"
    assert p1_data["unitMeasurement"] == "pack (10 pcs)"  # based on first sku which is sku1
    assert p1_data["image"] == "@/customer_dashboard/customer_assets/GI Pipe.png"
    assert p1_data["startingPrice"] == 12.0

    # Valve (unit = 1 -> piece, min price 50.0)
    p2_data = next(d for d in data if d["pid"] == "P2")
    assert p2_data["unitMeasurement"] == "piece"
    assert p2_data["startingPrice"] == 50.0

    # Empty
    p3_data = next(d for d in data if d["pid"] == "P3")
    assert p3_data["startingPrice"] == 0.0
    assert p3_data["unitMeasurement"] == "piece"


def test_product_detail_returns_product_and_skus(client, app):
    with app.app_context():
        v = Vendor(vid="V1", vendor_name="Vendor", vendor_prefix="V1")
        p = Product(pid="P1", pname="Screw", category="Hardware")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku = SKU(
            skuid="S1",
            vpid="VP1",
            current_sell_rate=Decimal("2.50"),
            current_buy_rate=Decimal("1.00"),
            specs=json.dumps({"size": "m4", "length": "10mm"}),
            stock_qty=100
        )
        sku_no_specs = SKU(
            skuid="S2",
            vpid="VP1",
            current_sell_rate=Decimal("3.00"),
            specs="Standard",
            stock_qty=50
        )
        
        db.session.add_all([v, p, vp, sku, sku_no_specs])
        db.session.commit()

    response = client.get("/api/customer/products/P1")
    assert response.status_code == 200
    data = response.get_json()

    assert data["product"]["pid"] == "P1"
    assert data["product"]["pName"] == "Screw"
    assert data["product"]["unitMeasurement"] == "piece"
    
    skus = data["skus"]
    assert len(skus) == 2
    
    sku1_data = next(s for s in skus if s["skuId"] == "S1")
    assert sku1_data["currentSell"] == 2.5
    assert sku1_data["currentBuy"] == 1.0
    assert sku1_data["specs"] == "m4 10mm"
    assert sku1_data["stockQty"] == 100

    sku2_data = next(s for s in skus if s["skuId"] == "S2")
    assert sku2_data["specs"] == "Standard"


def test_product_detail_not_found(client):
    response = client.get("/api/customer/products/INVALID")
    assert response.status_code == 404
    assert response.get_json()["message"] == "Product not found"


def test_customer_invoices_list(client, app):
    with app.app_context():
        c = Customer(cid="C1", customer_name="Test Customer")
        co = CustomerOrder(coid="CO1", cid="C1")
        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(
            cinv_id="INV1",
            psid="PS1",
            invoice_date=datetime(2023, 1, 1).date(),
            total_amount=Decimal("100.00"),
            status="Paid"
        )
        
        v = Vendor(vid="V1", vendor_name="V1", vendor_prefix="V1")
        p1 = Product(pid="P1", pname="Prod A", category="C")
        vp1 = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku1 = SKU(skuid="S1", vpid="VP1")
        
        # Second invoice for same customer, with multiple details to trigger "..." truncation
        co2 = CustomerOrder(coid="CO2", cid="C1")
        ps2 = PackingSlip(psid="PS2", coid="CO2")
        inv2 = CustomerInvoice(
            cinv_id="INV2",
            psid="PS2",
            invoice_date=datetime(2023, 1, 2).date()
        )
        
        p2 = Product(pid="P2", pname="Prod B", category="C")
        vp2 = VendorProduct(vpid="VP2", vid="V1", pid="P2")
        sku2 = SKU(skuid="S2", vpid="VP2")
        
        p3 = Product(pid="P3", pname="Prod C", category="C")
        vp3 = VendorProduct(vpid="VP3", vid="V1", pid="P3")
        sku3 = SKU(skuid="S3", vpid="VP3")
        
        p4 = Product(pid="P4", pname="Prod D", category="C")
        vp4 = VendorProduct(vpid="VP4", vid="V1", pid="P4")
        sku4 = SKU(skuid="S4", vpid="VP4")
        
        inv2_d1 = CustomerInvDetail(cdetail_id="ID1", cinv_id="INV2", skuid="S1")
        inv2_d2 = CustomerInvDetail(cdetail_id="ID2", cinv_id="INV2", skuid="S2")
        inv2_d3 = CustomerInvDetail(cdetail_id="ID3", cinv_id="INV2", skuid="S3")
        inv2_d4 = CustomerInvDetail(cdetail_id="ID4", cinv_id="INV2", skuid="S4")

        # Third invoice for receipt check
        co3 = CustomerOrder(coid="CO3", cid="C1")
        ps3 = PackingSlip(psid="PS3", coid="CO3")
        inv3 = CustomerInvoice(cinv_id="INV3", psid="PS3")
        dr = DeliveryReceipt(receipt_id="DR1", cinv_id="INV3")

        db.session.add_all([
            c, co, ps, inv, v, p1, vp1, sku1,
            co2, ps2, inv2, p2, vp2, sku2, p3, vp3, sku3, p4, vp4, sku4,
            inv2_d1, inv2_d2, inv2_d3, inv2_d4,
            co3, ps3, inv3, dr
        ])
        db.session.commit()

    response = client.get("/api/customer/invoices?cid=C1")
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 3
    # Check truncation (Prod A, Prod B, Prod C...)
    inv2_data = next(d for d in data if d["cInvId"] == "INV2")
    assert "Prod A, Prod B, Prod C..." in inv2_data["itemsSummary"]
    assert inv2_data["status"] == "Unpaid" # Default

    inv3_data = next(d for d in data if d["cInvId"] == "INV3")
    assert inv3_data["isReceived"] == True


def test_customer_invoices_missing_cid(client):
    response = client.get("/api/customer/invoices")
    assert response.status_code == 400
    assert response.get_json()["message"] == "Customer ID is required"


def test_customer_invoice_detail(client, app):
    with app.app_context():
        v = Vendor(vid="V1", vendor_name="V1", vendor_prefix="V1")
        p = Product(pid="P1", pname="Test Prod", category="C")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku = SKU(skuid="S1", vpid="VP1", specs="Spec1")

        c = Customer(cid="C1", customer_name="Customer")
        co = CustomerOrder(coid="CO1", cid="C1")
        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(
            cinv_id="INV1",
            psid="PS1",
            invoice_date=datetime(2023, 5, 5).date(),
            total_amount=Decimal("200.00"),
            status="Paid"
        )
        inv_d = CustomerInvDetail(
            cdetail_id="CD1",
            cinv_id="INV1",
            skuid="S1",
            ordered_qty=10,
            delivered_qty=8,
            sale_price=Decimal("25.00"),
            amount=Decimal("200.00")
        )
        
        u = User(uid="U1", full_name="Receiver")
        dr = DeliveryReceipt(receipt_id="DR1", cinv_id="INV1", received_by="U1", notes="All good", received_date=datetime(2023, 5, 6).date())

        db.session.add_all([v, p, vp, sku, c, co, ps, inv, inv_d, u, dr])
        db.session.commit()

    response = client.get("/api/customer/invoices/INV1")
    assert response.status_code == 200
    data = response.get_json()

    assert data["invoice"]["cInvId"] == "INV1"
    assert data["invoice"]["coId"] == "CO1"
    assert data["invoice"]["totalAmount"] == 200.0
    assert data["invoice"]["status"] == "Paid"
    assert data["invoice"]["receipt"]["notes"] == "All good"
    assert data["invoice"]["receipt"]["receivedBy"] == "Receiver"

    assert len(data["items"]) == 1
    assert data["items"][0]["orderedQty"] == 10
    assert data["items"][0]["salePrice"] == 25.0
    assert data["items"][0]["sku"]["specs"] == "Spec1"
    assert data["items"][0]["product"]["pName"] == "Test Prod"


def test_customer_invoice_detail_not_found(client):
    response = client.get("/api/customer/invoices/INVALID")
    assert response.status_code == 404
    assert response.get_json()["message"] == "Invoice not found"


def test_customer_order_detail(client, app):
    with app.app_context():
        c = Customer(cid="C1", customer_name="Customer")
        co = CustomerOrder(
            coid="CO1",
            cid="C1",
            order_date=datetime(2023, 8, 1).date(),
            status="Shipped",
            total_amount=Decimal("500.00")
        )
        
        v = Vendor(vid="V1", vendor_name="V1", vendor_prefix="V1")
        p = Product(pid="P1", pname="Prod X", category="C")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku = SKU(skuid="S1", vpid="VP1", specs=json.dumps({"s": "X"}))

        cod = CustomerOrderDetail(
            codid="COD1",
            coid="CO1",
            skuid="S1",
            quantity=5,
            amount=Decimal("500.00")
        )

        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(cinv_id="INV1", psid="PS1", status="Paid")
        inv_d = CustomerInvDetail(cdetail_id="CD1", cinv_id="INV1", skuid="S1", delivered_qty=2)

        inv2 = CustomerInvoice(cinv_id="INV2", psid="PS1", status="Unpaid")
        inv_d2 = CustomerInvDetail(cdetail_id="CD2", cinv_id="INV2", skuid="S1", delivered_qty=3)
        
        db.session.add_all([c, co, v, p, vp, sku, cod, ps, inv, inv_d, inv2, inv_d2])
        db.session.commit()

    response = client.get("/api/customer/orders/CO1")
    assert response.status_code == 200
    data = response.get_json()

    assert data["order"]["coId"] == "CO1"
    assert data["order"]["status"] == "Shipped"
    assert data["totalAmount"] == 500.0
    
    assert len(data["invoices"]) == 2
    
    assert len(data["items"]) == 1
    # total delivered qty should be sum of 2 + 3 = 5
    assert data["items"][0]["deliveredQty"] == 5
    assert data["items"][0]["orderedQty"] == 5
    assert data["items"][0]["salePrice"] == 100.0 # 500 / 5
    assert data["items"][0]["sku"]["specs"] == "X"


def test_customer_order_detail_not_found(client):
    response = client.get("/api/customer/orders/INVALID")
    assert response.status_code == 404
    assert response.get_json()["message"] == "Order not found"


def test_customer_orders_list(client, app):
    with app.app_context():
        c = Customer(cid="C1", customer_name="Customer")
        co = CustomerOrder(coid="CO1", cid="C1", total_amount=Decimal("20.00"))
        
        v = Vendor(vid="V1", vendor_name="V1", vendor_prefix="V1")
        p = Product(pid="P1", pname="Test", category="C")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku = SKU(skuid="S1", vpid="VP1")
        
        cod = CustomerOrderDetail(codid="COD1", coid="CO1", skuid="S1", quantity=3)

        db.session.add_all([c, co, v, p, vp, sku, cod])
        db.session.commit()
        
    response = client.get("/api/customer/orders?cid=C1")
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]["order"]["coId"] == "CO1"
    assert data[0]["totalAmount"] == 20.0
    assert len(data[0]["items"]) == 1
    assert data[0]["items"][0]["quantity"] == 3


def test_customer_orders_missing_cid(client):
    response = client.get("/api/customer/orders")
    assert response.status_code == 400


def test_place_order(client, app):
    with app.app_context():
        c = Customer(cid="C1", customer_name="Customer", uid="U1")
        sku = SKU(skuid="S1", current_sell_rate=Decimal("15.00"), stock_qty=10)
        sku2 = SKU(skuid="S2", current_sell_rate=Decimal("10.00"), stock_qty=10)
        
        db.session.add_all([c, sku, sku2])
        db.session.commit()

    payload = {
        "cid": "C1",
        "items": [
            {"skuId": "S1", "quantity": 2},
            {"skuId": "S2", "quantity": 0}, # Should be ignored
            {"skuId": "INVALID", "quantity": 1} # Should be ignored without errors
        ]
    }
    
    response = client.post("/api/customer/orders", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Order placed successfully"
    order_id = data["order_id"]
    
    with app.app_context():
        order = CustomerOrder.query.get(order_id)
        assert order is not None
        assert order.total_amount == Decimal("30.00") # 2 * 15.00
        
        details = CustomerOrderDetail.query.filter_by(coid=order_id).all()
        assert len(details) == 1
        assert details[0].skuid == "S1"
        assert details[0].quantity == 2


def test_place_order_invalid_payloads(client, app):
    # missing cid
    response = client.post("/api/customer/orders", json={"items": []})
    assert response.status_code == 400
    
    # missing items
    response = client.post("/api/customer/orders", json={"cid": "C1"})
    assert response.status_code == 400

    # invalid customer
    response = client.post("/api/customer/orders", json={"cid": "INVALID", "items": [{"skuId": "S1", "quantity": 1}]})
    assert response.status_code == 404


def test_customer_items_list(client, app):
    with app.app_context():
        c = Customer(cid="C1", customer_name="Customer")
        co = CustomerOrder(coid="CO1", cid="C1")
        cod = CustomerOrderDetail(codid="COD1", coid="CO1", skuid="S1", quantity=5)
        cod2 = CustomerOrderDetail(codid="COD2", coid="CO1", skuid="S2", quantity=2)
        
        # sku2 has delivery -> Shipped
        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(cinv_id="INV1", psid="PS1")
        inv_d = CustomerInvDetail(cdetail_id="CD1", cinv_id="INV1", skuid="S2", delivered_qty=2)

        v = Vendor(vid="V1", vendor_name="V1", vendor_prefix="V1")
        p = Product(pid="P1", pname="Prod", category="C")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku = SKU(skuid="S1", vpid="VP1")
        sku2 = SKU(skuid="S2", vpid="VP1")

        db.session.add_all([c, co, cod, cod2, ps, inv, inv_d, v, p, vp, sku, sku2])
        db.session.commit()

    response = client.get("/api/customer/items?cid=C1")
    assert response.status_code == 200
    data = response.get_json()
    
    assert len(data) == 2
    
    item1 = next(i for i in data if i["codId"] == "COD1")
    assert item1["status"] == "Confirmed" # No invoice details
    
    item2 = next(i for i in data if i["codId"] == "COD2")
    assert item2["status"] == "Shipped" # Has invoice details


def test_customer_items_missing_cid(client):
    response = client.get("/api/customer/items")
    assert response.status_code == 400


def test_customer_item_detail_timeline(client, app):
    with app.app_context():
        c = Customer(cid="C1", customer_name="Customer")
        co = CustomerOrder(coid="CO1", cid="C1", order_date=datetime(2023, 1, 1).date())
        
        v = Vendor(vid="V1", vendor_name="V1", vendor_prefix="V1")
        p = Product(pid="P1", pname="Timeline Prod", category="C")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        sku = SKU(skuid="S1", vpid="VP1", specs=json.dumps({"size": "10"}))

        cod = CustomerOrderDetail(codid="COD1", coid="CO1", skuid="S1", quantity=10, amount=Decimal("100.00"))

        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(cinv_id="INV1", psid="PS1", invoice_date=datetime(2023, 1, 2).date())
        inv_d = CustomerInvDetail(cdetail_id="CD1", cinv_id="INV1", skuid="S1", delivered_qty=5)

        dr = DeliveryReceipt(receipt_id="DR1", cinv_id="INV1", received_date=datetime(2023, 1, 3).date())
        dr_d = DeliveryReceiptDetail(dr_detail_id="DRD1", receipt_id="DR1", skuid="S1", received_qty=3)
        
        db.session.add_all([c, co, v, p, vp, sku, cod, ps, inv, inv_d, dr, dr_d])
        db.session.commit()

    response = client.get("/api/customer/items/COD1")
    assert response.status_code == 200
    data = response.get_json()

    assert data["codId"] == "COD1"
    assert data["coId"] == "CO1"
    assert data["product"]["pName"] == "Timeline Prod"
    assert data["product"]["specs"] == "10"
    
    timeline = data["timeline"]
    # timeline should have 3 segments
    # Confirmed, Shipped, Received
    assert len(timeline) == 3
    
    assert timeline[0]["status"] == "Confirmed"
    assert timeline[0]["completed"] == True

    assert timeline[1]["status"] == "Shipped"
    assert timeline[1]["completed"] == True
    assert timeline[1]["qty"] == 5

    assert timeline[2]["status"] == "Received"
    assert timeline[2]["completed"] == True
    assert timeline[2]["qty"] == 3


def test_customer_item_detail_not_found(client):
    response = client.get("/api/customer/items/INVALID")
    assert response.status_code == 404


def test_customer_receive_success(client, app):
    with app.app_context():
        co = CustomerOrder(coid="CO1", cid="C1")
        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(cinv_id="INV1", psid="PS1")
        inv_d1 = CustomerInvDetail(cdetail_id="CD1", cinv_id="INV1", skuid="S1", delivered_qty=4)
        inv_d2 = CustomerInvDetail(cdetail_id="CD2", cinv_id="INV1", skuid="S2", delivered_qty=6)

        db.session.add_all([co, ps, inv, inv_d1, inv_d2])
        db.session.commit()

    payload = {
        "cinv_id": "INV1",
        "uid": "U1",
        "notes": "Looks good",
        "items": [
            {"skuid": "S1", "received_qty": 4, "condition": "Good"},
            {"skuid": "S2", "received_qty": 5, "condition": "Damaged"}
        ]
    }
    
    response = client.post("/api/customer/receive", json=payload)
    assert response.status_code == 201
    
    with app.app_context():
        receipt = DeliveryReceipt.query.filter_by(cinv_id="INV1").first()
        assert receipt is not None
        assert receipt.notes == "Looks good"
        
        details = DeliveryReceiptDetail.query.filter_by(receipt_id=receipt.receipt_id).all()
        assert len(details) == 2
        d1 = next(d for d in details if d.skuid == "S1")
        assert d1.received_qty == 4
        assert d1.condition == "Good"
        
        d2 = next(d for d in details if d.skuid == "S2")
        assert d2.received_qty == 5
        assert d2.condition == "Damaged"


def test_customer_receive_default_items(client, app):
    with app.app_context():
        co = CustomerOrder(coid="CO1", cid="C1")
        ps = PackingSlip(psid="PS1", coid="CO1")
        inv = CustomerInvoice(cinv_id="INV1", psid="PS1")
        inv_d1 = CustomerInvDetail(cdetail_id="CD1", cinv_id="INV1", skuid="S1", delivered_qty=4)
        
        db.session.add_all([co, ps, inv, inv_d1])
        db.session.commit()

    payload = {
        "cinv_id": "INV1",
        "uid": "U1"
    }
    
    response = client.post("/api/customer/receive", json=payload)
    assert response.status_code == 201
    
    with app.app_context():
        receipt = DeliveryReceipt.query.filter_by(cinv_id="INV1").first()
        assert receipt is not None
        details = DeliveryReceiptDetail.query.filter_by(receipt_id=receipt.receipt_id).all()
        assert len(details) == 1
        assert details[0].received_qty == 4
        assert details[0].condition == "Good"


def test_customer_receive_invalid_payloads(client, app):
    # Missing args
    response = client.post("/api/customer/receive", json={})
    assert response.status_code == 400

    # Invoice not found
    response = client.post("/api/customer/receive", json={"cinv_id": "INVALID", "uid": "U1"})
    assert response.status_code == 404

    # Already received
    with app.app_context():
        inv = CustomerInvoice(cinv_id="INV2")
        dr = DeliveryReceipt(receipt_id="DR2", cinv_id="INV2")
        db.session.add_all([inv, dr])
        db.session.commit()
    
    response = client.post("/api/customer/receive", json={"cinv_id": "INV2", "uid": "U1"})
    assert response.status_code == 400
    assert response.get_json()["message"] == "Receipt already confirmed for this invoice"
