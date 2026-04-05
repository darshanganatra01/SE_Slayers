"""Tests for Internal Portal – Orders page APIs.

Covers:
  GET  /api/internal-portal/orders
  POST /api/internal-portal/pack
  POST /api/internal-portal/unpack
  POST /api/internal-portal/ship
  POST /api/internal-portal/receive
  POST /api/internal-portal/create-order
  GET  /api/internal-portal/new-order-data
  GET  /api/internal-portal/product-skus/<pid>
"""

from datetime import date
from decimal import Decimal

from app import db
from app.models.customer import Customer
from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
from app.models.customer_order import CustomerOrder
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.delivery_receipt import DeliveryReceipt, DeliveryReceiptDetail
from app.models.packing_slip import PackingSlip, PackingSlipDetail
from app.models.payment import Payment
from app.models.product import Product
from app.models.sku import SKU
from app.models.user import User
from app.models.vendor import Vendor, VendorProduct


# ── Helpers ────────────────────────────────────────────────────────

def _admin():
    admin = User(
        uid="USR-ADMIN01",
        full_name="Metro Business Owner",
        email="owner@metrohardware.com",
        role=User.ROLE_ADMIN,
        is_active=True,
    )
    admin.set_password("password123")
    return admin


def _customer_user(uid="USR-CUST01", email="customer@example.com", name="Sample Customer"):
    user = User(
        uid=uid,
        full_name=name,
        email=email,
        role=User.ROLE_CUSTOMER,
        is_active=True,
    )
    user.set_password("password123")
    return user


def _customer(cid="C-001", uid="USR-CUST01", name="Raj Hardware", acp=15):
    return Customer(
        cid=cid, uid=uid, customer_name=name, acp=acp,
        location="Rajkot", contact="9999999999", email="raj@example.com",
    )


def _product_chain(vid="V-1", pid="P-1", vpid="VP-1", skuid="SKU-1",
                    sell_rate="50.00", buy_rate="30.00", stock=100,
                    pname="SS Step Nipple", threshold=10,
                    unit_sell=1, lot_sell=1):
    """Create Vendor -> Product -> VendorProduct -> SKU chain."""
    vendor = Vendor(vid=vid, vendor_name="Amul Engineering", vendor_prefix="AM")
    product = Product(pid=pid, pname=pname, category="Pipe Fittings")
    vp = VendorProduct(vpid=vpid, vid=vid, pid=pid)
    sku = SKU(
        skuid=skuid, vpid=vpid,
        current_sell_rate=Decimal(sell_rate),
        current_buy_rate=Decimal(buy_rate),
        stock_qty=stock, threshold=threshold,
        unit_measurement_sell=unit_sell, lot_size_sell=lot_sell,
        specs={"spec1": "63 mm", "spec2": "Clamp 2.5mm"},
    )
    return vendor, product, vp, sku


def _confirmed_order(cid="C-001", coid="CO-001", skuid="SKU-1", qty=10,
                     unit_price=50.0, admin_uid="USR-ADMIN01"):
    """Create a Confirmed order with line item details."""
    order = CustomerOrder(
        coid=coid, cid=cid, created_by=admin_uid,
        order_date=date.today(), status="Confirmed",
        priority="High", total_amount=Decimal(str(qty * unit_price)),
    )
    detail = CustomerOrderDetail(
        codid=f"COD-{coid}", coid=coid, skuid=skuid,
        quantity=qty, amount=Decimal(str(qty * unit_price)),
    )
    return order, detail


# ═══════════════════════════════════════════════════════════════════
# GET /api/internal-portal/orders
# ═══════════════════════════════════════════════════════════════════

class TestOrdersListEndpoint:
    """Tests for the internal orders listing."""

    def test_returns_empty_orders_when_no_orders_exist(self, client, app):
        """Endpoint returns empty orders and inventory when DB is empty."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["orders"] == []
        assert payload["inventory"] == {}

    def test_confirmed_order_appears_in_inprocess_bucket(self, client, app):
        """A confirmed order with no packing slips should be in the 'inprocess' bucket."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        orders = response.get_json()["orders"]
        assert len(orders) == 1
        assert orders[0]["status"] == "inprocess"
        assert orders[0]["customer"] == "Raj Hardware"
        assert len(orders[0]["items"]) == 1
        assert orders[0]["items"][0]["qty"] == 10

    def test_fully_packed_order_appears_in_packed_bucket_only(self, client, app):
        """A fully packed order should only have a 'packed' card (not inprocess)."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])

            # Pack all 5
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([slip, slip_d])
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        orders = response.get_json()["orders"]
        # Should only have packed bucket, no inprocess (all packed)
        statuses = [o["status"] for o in orders]
        assert "packed" in statuses
        assert "inprocess" not in statuses

    def test_partially_packed_order_appears_in_both_inprocess_and_packed(self, client, app):
        """A partially packed order should generate both inprocess and packed cards."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=10)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])

            # Pack only 4 of 10
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=4,
            )
            db.session.add_all([slip, slip_d])
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        orders = response.get_json()["orders"]
        statuses = {o["status"] for o in orders}
        assert statuses == {"inprocess", "packed"}
        # In-process should have remaining 6
        ip_order = next(o for o in orders if o["status"] == "inprocess")
        assert ip_order["items"][0]["qty"] == 6
        # Packed should have 4
        p_order = next(o for o in orders if o["status"] == "packed")
        assert p_order["items"][0]["qty"] == 4

    def test_shipped_order_appears_in_shipped_bucket(self, client, app):
        """A shipped order should appear in the 'shipped' bucket."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])

            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            inv = CustomerInvoice(
                cinv_id="INV-001", pslip_id="PS-001",
                created_by="USR-ADMIN01", invoice_date=date.today(),
                status="Unpaid", total_amount=Decimal("250.00"),
            )
            inv_d = CustomerInvDetail(
                cdetail_id="CD-001", cinv_id="INV-001",
                skuid="SKU-1", ordered_qty=5, delivered_qty=5,
                sale_price=Decimal("50.00"), amount=Decimal("250.00"),
            )
            db.session.add_all([slip, slip_d, inv, inv_d])
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        orders = response.get_json()["orders"]
        shipped = [o for o in orders if o["status"] == "shipped"]
        assert len(shipped) == 1
        assert shipped[0]["items"][0]["qty"] == 5

    def test_inventory_data_populated_for_order_items(self, client, app):
        """Inventory dict should contain stock levels for items in orders."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain(stock=42, threshold=10)
            order, detail = _confirmed_order()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        inventory = response.get_json()["inventory"]
        assert len(inventory) > 0
        # The key format is "ProductName (ID: SKUID)"
        key = "SS Step Nipple (ID: SKU-1)"
        assert inventory[key]["stock"] == 42
        assert inventory[key]["max"] == 10

    def test_order_priority_derived_from_customer_acp(self, client, app):
        """Order priority should be mapped from customer ACP: <=15->High, <=30->Medium, >30->Low."""
        with app.app_context():
            admin = _admin()
            # High priority customer (acp=10)
            u1 = _customer_user(uid="USR-C1", email="c1@test.com")
            c1 = _customer(cid="C-HIGH", uid="USR-C1", name="VIP Customer", acp=10)
            # Low priority customer (acp=45)
            u2 = _customer_user(uid="USR-C2", email="c2@test.com")
            c2 = _customer(cid="C-LOW", uid="USR-C2", name="Casual Customer", acp=45)
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, u1, u2, c1, c2, vendor, product, vp, sku])

            o1, d1 = _confirmed_order(cid="C-HIGH", coid="CO-H")
            o2, d2 = _confirmed_order(cid="C-LOW", coid="CO-L")
            db.session.add_all([o1, d1, o2, d2])
            db.session.commit()

        response = client.get("/api/internal-portal/orders")

        assert response.status_code == 200
        orders = response.get_json()["orders"]
        priority_map = {o["id"]: o["priority"] for o in orders}
        assert priority_map["CO-H"] == "High"
        assert priority_map["CO-L"] == "Low"


# ═══════════════════════════════════════════════════════════════════
# POST /api/internal-portal/pack
# ═══════════════════════════════════════════════════════════════════

class TestPackEndpoint:
    """Tests for order packing."""

    def test_pack_creates_packing_slip_and_updates_order_status(self, client, app):
        """Packing items creates a slip and transitions order to PartiallyPacked."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=10)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-001", "items": [{"skuid": "SKU-1", "packed_qty": 5}]},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "PartiallyPacked"
        assert "pslip_id" in payload

    def test_pack_all_items_sets_status_to_fully_packed(self, client, app):
        """Packing all ordered items should set order status to FullyPacked."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-001", "items": [{"skuid": "SKU-1", "packed_qty": 5}]},
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == "FullyPacked"

    def test_pack_rejects_quantity_exceeding_ordered(self, client, app):
        """Cannot pack more than the ordered quantity."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-001", "items": [{"skuid": "SKU-1", "packed_qty": 10}]},
        )

        assert response.status_code == 400
        assert "exceeds ordered quantity" in response.get_json()["message"]

    def test_pack_cumulative_validation_across_multiple_slips(self, client, app):
        """Second packing should be validated against previously packed quantities."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=8)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        # First pack: 5 of 8
        r1 = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-001", "items": [{"skuid": "SKU-1", "packed_qty": 5}]},
        )
        assert r1.status_code == 200

        # Second pack: 5 more -> total 10 > 8, should fail
        r2 = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-001", "items": [{"skuid": "SKU-1", "packed_qty": 5}]},
        )
        assert r2.status_code == 400

    def test_pack_nonexistent_order_returns_404(self, client, app):
        """Packing a non-existent order ID should return 404."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-FAKE", "items": [{"skuid": "SKU-1", "packed_qty": 1}]},
        )

        assert response.status_code == 404

    def test_pack_without_order_id_returns_400(self, client, app):
        """Missing coid in the request body should return 400."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/pack",
            json={"items": [{"skuid": "SKU-1", "packed_qty": 1}]},
        )

        assert response.status_code == 400

    def test_pack_strips_status_suffix_from_order_id(self, client, app):
        """Order IDs with -P or -S suffixes should be stripped to find the original order."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=10)
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku, order, detail])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/pack",
            json={"coid": "CO-001-P", "items": [{"skuid": "SKU-1", "packed_qty": 3}]},
        )

        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# POST /api/internal-portal/unpack
# ═══════════════════════════════════════════════════════════════════

class TestUnpackEndpoint:
    """Tests for unpacking/reverting a packing slip."""

    def test_unpack_deletes_slip_and_reverts_order_status(self, client, app):
        """Unpacking the only slip should revert order status to Confirmed."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=10)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/unpack",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 200
        assert response.get_json()["message"] == "Unpacked successfully"

        # Verify order status reverted
        with app.app_context():
            order = CustomerOrder.query.get("CO-001")
            assert order.status == "Confirmed"
            assert PackingSlip.query.count() == 0
            assert PackingSlipDetail.query.count() == 0

    def test_unpack_shipped_slip_rejected(self, client, app):
        """Cannot unpack a slip that has already been shipped."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/unpack",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 400
        assert "Cannot unpack a shipped batch" in response.get_json()["message"]

    def test_unpack_nonexistent_slip_returns_404(self, client, app):
        """Attempting to unpack a non-existent slip returns 404."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/unpack",
            json={"pslip_id": "PS-FAKE"},
        )

        assert response.status_code == 404

    def test_unpack_missing_id_returns_400(self, client, app):
        """Missing pslip_id should return 400."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post("/api/internal-portal/unpack", json={})

        assert response.status_code == 400

    def test_unpack_one_of_multiple_slips_keeps_partially_packed(self, client, app):
        """Unpacking one of two slips should keep order as PartiallyPacked."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=10)
            slip1 = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip1_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=3,
            )
            slip2 = PackingSlip(
                pslip_id="PS-002", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip2_d = PackingSlipDetail(
                psd_id="PSD-002", pslip_id="PS-002",
                skuid="SKU-1", packed_qty=4,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip1, slip1_d, slip2, slip2_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/unpack",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 200
        with app.app_context():
            order = CustomerOrder.query.get("CO-001")
            assert order.status == "PartiallyPacked"


# ═══════════════════════════════════════════════════════════════════
# POST /api/internal-portal/ship
# ═══════════════════════════════════════════════════════════════════

class TestShipEndpoint:
    """Tests for shipping a packed batch."""

    def test_ship_creates_invoice_and_deducts_stock(self, client, app):
        """Shipping creates an invoice, marks slip as Shipped, and deducts stock."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain(stock=50)
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/ship",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert "cinv_id" in payload

        with app.app_context():
            slip = PackingSlip.query.get("PS-001")
            assert slip.status == "Shipped"
            sku = SKU.query.get("SKU-1")
            assert sku.stock_qty == 45  # 50 - 5 * 1 * 1

    def test_ship_respects_unit_measurement_and_lot_size(self, client, app):
        """Stock deduction should factor in unit_measurement_sell * lot_size_sell."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            # unit_sell=2, lot_sell=3 -> each packed_qty deducts 2*3=6 units
            vendor, product, vp, sku = _product_chain(
                stock=100, unit_sell=2, lot_sell=3,
            )
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/ship",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 200
        with app.app_context():
            sku = SKU.query.get("SKU-1")
            assert sku.stock_qty == 70  # 100 - 5 * 2 * 3 = 70

    def test_ship_rejects_insufficient_stock(self, client, app):
        """Shipping should fail when stock is not sufficient for the deduction."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain(stock=3)
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/ship",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 400
        assert "Stock is not sufficient" in response.get_json()["message"]

    def test_ship_already_shipped_returns_400(self, client, app):
        """Shipping an already-shipped slip should return 400."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/ship",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 400
        assert "Already shipped" in response.get_json()["message"]

    def test_ship_completes_order_when_all_items_delivered(self, client, app):
        """Order status should be Completed if shipped qty matches ordered qty."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain(stock=100)
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/ship",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == "Completed"

    def test_ship_partial_delivery_sets_partially_fulfilled(self, client, app):
        """Shipping partial quantity should set order to PartiallyFulfilled."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain(stock=100)
            order, detail = _confirmed_order(qty=10)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Packed",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/ship",
            json={"pslip_id": "PS-001"},
        )

        assert response.status_code == 200
        assert response.get_json()["status"] == "PartiallyFulfilled"


# ═══════════════════════════════════════════════════════════════════
# POST /api/internal-portal/receive
# ═══════════════════════════════════════════════════════════════════

class TestReceiveEndpoint:
    """Tests for marking an invoice as received."""

    def test_receive_creates_delivery_receipt(self, client, app):
        """Marking received creates a DeliveryReceipt with all invoice items."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            inv = CustomerInvoice(
                cinv_id="INV-001", pslip_id="PS-001",
                created_by="USR-ADMIN01", invoice_date=date.today(),
                status="Unpaid", total_amount=Decimal("250.00"),
            )
            inv_d = CustomerInvDetail(
                cdetail_id="CD-001", cinv_id="INV-001",
                skuid="SKU-1", ordered_qty=5, delivered_qty=5,
                sale_price=Decimal("50.00"), amount=Decimal("250.00"),
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d, inv, inv_d])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/receive",
            json={"cinv_id": "INV-001", "uid": "USR-ADMIN01"},
        )

        assert response.status_code == 201
        assert "receipt_id" in response.get_json()

        with app.app_context():
            receipt = DeliveryReceipt.query.first()
            assert receipt is not None
            assert receipt.cinv_id == "INV-001"
            details = list(receipt.details)
            assert len(details) == 1
            assert details[0].received_qty == 5
            assert details[0].condition == "Good"

    def test_receive_duplicate_returns_400(self, client, app):
        """Cannot receive the same invoice twice."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            order, detail = _confirmed_order(qty=5)
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=5,
            )
            inv = CustomerInvoice(
                cinv_id="INV-001", pslip_id="PS-001",
                created_by="USR-ADMIN01", invoice_date=date.today(),
                status="Unpaid", total_amount=Decimal("250.00"),
            )
            inv_d = CustomerInvDetail(
                cdetail_id="CD-001", cinv_id="INV-001",
                skuid="SKU-1", ordered_qty=5, delivered_qty=5,
                sale_price=Decimal("50.00"), amount=Decimal("250.00"),
            )
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku,
                                order, detail, slip, slip_d, inv, inv_d])
            db.session.commit()

        # First receive
        r1 = client.post(
            "/api/internal-portal/receive",
            json={"cinv_id": "INV-001", "uid": "USR-ADMIN01"},
        )
        assert r1.status_code == 201

        # Duplicate
        r2 = client.post(
            "/api/internal-portal/receive",
            json={"cinv_id": "INV-001", "uid": "USR-ADMIN01"},
        )
        assert r2.status_code == 400
        assert "already confirmed" in r2.get_json()["message"]

    def test_receive_nonexistent_invoice_returns_404(self, client, app):
        """Attempting to receive a non-existent invoice returns 404."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/receive",
            json={"cinv_id": "INV-FAKE", "uid": "USR-ADMIN01"},
        )

        assert response.status_code == 404

    def test_receive_missing_fields_returns_400(self, client, app):
        """Missing cinv_id or uid should return 400."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/receive",
            json={"cinv_id": "INV-001"},
        )

        assert response.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# POST /api/internal-portal/create-order
# ═══════════════════════════════════════════════════════════════════

class TestCreateOrderEndpoint:
    """Tests for creating new customer orders from internal portal."""

    def test_create_order_persists_order_and_details(self, client, app):
        """Successfully creating an order should persist the order and line items."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/create-order",
            json={
                "cid": "C-001",
                "items": [{"skuid": "SKU-1", "quantity": 10}],
            },
        )

        assert response.status_code == 201
        payload = response.get_json()
        assert "order_id" in payload
        assert payload["total"] == 500.0  # 10 * 50.00

        with app.app_context():
            order = CustomerOrder.query.get(payload["order_id"])
            assert order is not None
            assert order.cid == "C-001"
            assert order.status == "Confirmed"
            details = list(order.details)
            assert len(details) == 1
            assert details[0].quantity == 10

    def test_create_order_with_multiple_items(self, client, app):
        """Order with multiple line items should sum amounts correctly."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            v = Vendor(vid="V-1", vendor_name="Amul", vendor_prefix="AM")
            p1 = Product(pid="P-1", pname="Nipple", category="Fittings")
            p2 = Product(pid="P-2", pname="Clamp", category="Fittings")
            vp1 = VendorProduct(vpid="VP-1", vid="V-1", pid="P-1")
            vp2 = VendorProduct(vpid="VP-2", vid="V-1", pid="P-2")
            sku1 = SKU(skuid="SKU-1", vpid="VP-1", current_sell_rate=Decimal("50.00"),
                       stock_qty=100, specs={"spec1": "63 mm"})
            sku2 = SKU(skuid="SKU-2", vpid="VP-2", current_sell_rate=Decimal("30.00"),
                       stock_qty=200, specs={"spec1": "90 mm"})
            db.session.add_all([admin, cust_user, cust, v, p1, p2, vp1, vp2, sku1, sku2])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/create-order",
            json={
                "cid": "C-001",
                "items": [
                    {"skuid": "SKU-1", "quantity": 5},
                    {"skuid": "SKU-2", "quantity": 10},
                ],
            },
        )

        assert response.status_code == 201
        assert response.get_json()["total"] == 550.0  # 5*50 + 10*30

    def test_create_order_missing_customer_returns_404(self, client, app):
        """Creating an order for a non-existent customer returns 404."""
        with app.app_context():
            admin = _admin()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, vendor, product, vp, sku])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/create-order",
            json={"cid": "C-NONEXIST", "items": [{"skuid": "SKU-1", "quantity": 1}]},
        )

        assert response.status_code == 404

    def test_create_order_missing_items_returns_400(self, client, app):
        """Creating an order with no items should return 400."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            db.session.add_all([admin, cust_user, cust])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/create-order",
            json={"cid": "C-001", "items": []},
        )

        assert response.status_code == 400

    def test_create_order_missing_cid_returns_400(self, client, app):
        """Creating an order without customer ID should return 400."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/create-order",
            json={"items": [{"skuid": "SKU-1", "quantity": 1}]},
        )

        assert response.status_code == 400

    def test_create_order_sets_priority_from_customer_acp(self, client, app):
        """Order priority should be derived from the customer's ACP."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer(acp=10)  # ACP<=15 -> High
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/create-order",
            json={"cid": "C-001", "items": [{"skuid": "SKU-1", "quantity": 2}]},
        )

        assert response.status_code == 201
        with app.app_context():
            order = CustomerOrder.query.get(response.get_json()["order_id"])
            assert order.priority == "High"


# ═══════════════════════════════════════════════════════════════════
# GET /api/internal-portal/new-order-data
# ═══════════════════════════════════════════════════════════════════

class TestNewOrderDataEndpoint:
    """Tests for the new-order-data lookup endpoint."""

    def test_returns_customers_and_products(self, client, app):
        """Should return all customers and products for the order form."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            product = Product(pid="P-1", pname="SS Step Nipple", category="Pipe Fittings")
            db.session.add_all([admin, cust_user, cust, product])
            db.session.commit()

        response = client.get("/api/internal-portal/new-order-data")

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload["customers"]) == 1
        assert payload["customers"][0]["cid"] == "C-001"
        assert payload["customers"][0]["customer_name"] == "Raj Hardware"
        assert len(payload["products"]) == 1
        assert payload["products"][0]["pname"] == "SS Step Nipple"

    def test_returns_empty_when_no_data(self, client, app):
        """Should return empty lists when no customers or products exist."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.get("/api/internal-portal/new-order-data")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["customers"] == []
        assert payload["products"] == []


# ═══════════════════════════════════════════════════════════════════
# GET /api/internal-portal/product-skus/<pid>
# ═══════════════════════════════════════════════════════════════════

class TestProductSKUsEndpoint:
    """Tests for the product SKU variants lookup."""

    def test_returns_skus_for_product(self, client, app):
        """Should return all SKU variants for a given product."""
        with app.app_context():
            admin = _admin()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, vendor, product, vp, sku])
            db.session.commit()

        response = client.get("/api/internal-portal/product-skus/P-1")

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 1
        assert payload[0]["skuid"] == "SKU-1"
        assert payload[0]["sell_rate"] == 50.0
        assert payload[0]["stock_qty"] == 100

    def test_returns_empty_for_unknown_product(self, client, app):
        """Should return empty list for a product with no SKUs."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.get("/api/internal-portal/product-skus/P-NONEXIST")

        assert response.status_code == 200
        assert response.get_json() == []
