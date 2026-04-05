"""Tests for Internal Portal – Overview page API.

Covers:
  GET /api/internal-portal/overview
"""

from datetime import date, timedelta
from decimal import Decimal

from app import db
from app.models.customer import Customer
from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
from app.models.customer_order import CustomerOrder
from app.models.customer_order_detail import CustomerOrderDetail
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
        uid=uid, full_name=name, email=email,
        role=User.ROLE_CUSTOMER, is_active=True,
    )
    user.set_password("password123")
    return user


def _customer(cid="C-001", uid="USR-CUST01", name="Raj Hardware", acp=15):
    return Customer(
        cid=cid, uid=uid, customer_name=name, acp=acp,
        location="Rajkot", contact="9999999999", email="raj@example.com",
    )


def _product_chain(skuid="SKU-1", sell_rate="50.00", stock=100, threshold=10):
    vendor = Vendor(vid="V-1", vendor_name="Amul Engineering", vendor_prefix="AM")
    product = Product(pid="P-1", pname="SS Step Nipple", category="Pipe Fittings")
    vp = VendorProduct(vpid="VP-1", vid="V-1", pid="P-1")
    sku = SKU(
        skuid=skuid, vpid="VP-1",
        current_sell_rate=Decimal(sell_rate),
        stock_qty=stock, threshold=threshold,
        specs={"spec1": "63 mm", "spec2": "Clamp 2.5mm"},
    )
    return vendor, product, vp, sku


# ═══════════════════════════════════════════════════════════════════
# GET /api/internal-portal/overview
# ═══════════════════════════════════════════════════════════════════

class TestOverviewEndpoint:
    """Tests for the internal portal overview / dashboard metrics."""

    def test_overview_returns_all_metric_keys(self, client, app):
        """Verify the response structure includes all expected top-level keys."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        payload = response.get_json()
        assert "metrics" in payload
        assert "overdue" in payload
        assert "priorityOrders" in payload
        assert "activityFeed" in payload
        assert "lowStockItems" in payload

    def test_overview_empty_db_returns_zeroes(self, client, app):
        """With an empty database, all counts and values should be zero."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["metrics"]["pending"] == 0
        assert payload["metrics"]["highPriority"] == 0
        assert payload["metrics"]["lowStock"] == 0
        assert payload["metrics"]["quarterlyRevenue"] == 0
        assert payload["overdue"]["amount"] == 0
        assert payload["overdue"]["customers"] == 0
        assert payload["priorityOrders"] == []
        assert payload["lowStockItems"] == []

    def test_pending_orders_counted_correctly(self, client, app):
        """Orders not Completed/Cancelled/Dispatched should count as pending."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            # Pending statuses
            for i, status in enumerate(["Confirmed", "PartiallyPacked", "FullyPacked"]):
                o = CustomerOrder(
                    coid=f"CO-{i}", cid="C-001", created_by="USR-ADMIN01",
                    order_date=date.today(), status=status,
                    priority="Medium", total_amount=Decimal("100"),
                )
                db.session.add(o)

            # Non-pending statuses
            for i, status in enumerate(["Completed", "Cancelled", "Dispatched"]):
                o = CustomerOrder(
                    coid=f"CO-NP-{i}", cid="C-001", created_by="USR-ADMIN01",
                    order_date=date.today(), status=status,
                    priority="Medium", total_amount=Decimal("100"),
                )
                db.session.add(o)

            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        assert response.get_json()["metrics"]["pending"] == 3

    def test_high_priority_orders_counted_from_acp(self, client, app):
        """Orders where customer ACP <= 15 or priority is High should be counted."""
        with app.app_context():
            admin = _admin()
            # VIP customer (acp=10)
            u1 = _customer_user(uid="USR-C1", email="c1@test.com")
            c1 = _customer(cid="C-VIP", uid="USR-C1", acp=10)
            # Regular customer (acp=25)
            u2 = _customer_user(uid="USR-C2", email="c2@test.com")
            c2 = _customer(cid="C-REG", uid="USR-C2", acp=25)
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, u1, u2, c1, c2, vendor, product, vp, sku])

            o1 = CustomerOrder(
                coid="CO-1", cid="C-VIP", created_by="USR-ADMIN01",
                order_date=date.today(), status="Confirmed",
                priority="High", total_amount=Decimal("500"),
            )
            o2 = CustomerOrder(
                coid="CO-2", cid="C-REG", created_by="USR-ADMIN01",
                order_date=date.today(), status="Confirmed",
                priority="Medium", total_amount=Decimal("300"),
            )
            db.session.add_all([o1, o2])
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        assert response.get_json()["metrics"]["highPriority"] == 1

    def test_low_stock_count_and_items(self, client, app):
        """SKUs below their threshold should be counted and listed."""
        with app.app_context():
            admin = _admin()
            v = Vendor(vid="V-1", vendor_name="Amul", vendor_prefix="AM")
            p = Product(pid="P-1", pname="Nipple", category="Fittings")
            vp = VendorProduct(vpid="VP-1", vid="V-1", pid="P-1")
            db.session.add_all([admin, v, p, vp])

            # Below threshold
            sku1 = SKU(skuid="SKU-LOW", vpid="VP-1", stock_qty=2, threshold=10,
                       specs={"spec1": "63 mm"})
            # Above threshold
            sku2 = SKU(skuid="SKU-OK", vpid="VP-1", stock_qty=50, threshold=10,
                       specs={"spec1": "90 mm"})
            # Zero stock
            sku3 = SKU(skuid="SKU-ZERO", vpid="VP-1", stock_qty=0, threshold=5,
                       specs={"spec1": "110 mm"})
            db.session.add_all([sku1, sku2, sku3])
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["metrics"]["lowStock"] == 2  # SKU-LOW and SKU-ZERO
        assert len(payload["lowStockItems"]) == 2

    def test_quarterly_revenue_sums_recent_payments(self, client, app):
        """Quarterly revenue should sum all payments within the last 90 days."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            # Order + slip + invoice chain
            order = CustomerOrder(
                coid="CO-001", cid="C-001", created_by="USR-ADMIN01",
                order_date=date.today(), status="Completed",
                total_amount=Decimal("1000"),
            )
            detail = CustomerOrderDetail(
                codid="COD-001", coid="CO-001", skuid="SKU-1",
                quantity=20, amount=Decimal("1000"),
            )
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=20,
            )
            inv = CustomerInvoice(
                cinv_id="INV-001", pslip_id="PS-001",
                created_by="USR-ADMIN01", invoice_date=date.today(),
                status="Paid", total_amount=Decimal("1000"),
            )
            db.session.add_all([order, detail, slip, slip_d, inv])

            # Recent payment (within 90 days)
            p1 = Payment(
                payment_id="PAY-001", cinv_id="INV-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("600"), method="Cash",
            )
            # Old payment (over 90 days ago)
            p2 = Payment(
                payment_id="PAY-002", cinv_id="INV-001",
                recorded_by="USR-ADMIN01", payment_date=date.today() - timedelta(days=100),
                amount=Decimal("400"), method="Cash",
            )
            db.session.add_all([p1, p2])
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        assert response.get_json()["metrics"]["quarterlyRevenue"] == 600.0

    def test_overdue_invoices_calculated_from_acp(self, client, app):
        """Invoices outstanding beyond customer ACP should be flagged as overdue."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer(acp=15)  # If invoice > 15 days old and unpaid -> overdue
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            order = CustomerOrder(
                coid="CO-001", cid="C-001", created_by="USR-ADMIN01",
                order_date=date.today() - timedelta(days=30), status="Completed",
                total_amount=Decimal("500"),
            )
            detail = CustomerOrderDetail(
                codid="COD-001", coid="CO-001", skuid="SKU-1",
                quantity=10, amount=Decimal("500"),
            )
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today() - timedelta(days=25),
                status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=10,
            )
            # Invoice 20 days old, ACP=15 -> overdue
            inv = CustomerInvoice(
                cinv_id="INV-001", pslip_id="PS-001",
                created_by="USR-ADMIN01",
                invoice_date=date.today() - timedelta(days=20),
                status="Unpaid", total_amount=Decimal("500"),
            )
            inv_d = CustomerInvDetail(
                cdetail_id="CD-001", cinv_id="INV-001",
                skuid="SKU-1", ordered_qty=10, delivered_qty=10,
                sale_price=Decimal("50"), amount=Decimal("500"),
            )
            db.session.add_all([order, detail, slip, slip_d, inv, inv_d])
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        overdue = response.get_json()["overdue"]
        assert overdue["amount"] == 500.0
        assert overdue["customers"] == 1
        assert overdue["longestOutstanding"] == 20

    def test_priority_orders_sorted_by_acp_and_limited_to_five(self, client, app):
        """Priority orders should be sorted by ACP ascending and capped at 5."""
        with app.app_context():
            admin = _admin()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, vendor, product, vp, sku])

            for i in range(7):
                uid = f"USR-C{i}"
                u = _customer_user(uid=uid, email=f"c{i}@test.com")
                acp_val = 5 + i * 5  # 5, 10, 15, 20, 25, 30, 35
                c = _customer(cid=f"C-{i}", uid=uid, name=f"Cust-{i}", acp=acp_val)
                o = CustomerOrder(
                    coid=f"CO-{i}", cid=f"C-{i}", created_by="USR-ADMIN01",
                    order_date=date.today(), status="Confirmed",
                    priority="Medium", total_amount=Decimal("100"),
                )
                db.session.add_all([u, c, o])
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        priority_orders = response.get_json()["priorityOrders"]
        assert len(priority_orders) == 5
        # First should be lowest ACP
        assert priority_orders[0]["score"] == 5
        assert priority_orders[4]["score"] == 25

    def test_activity_feed_contains_orders_payments_and_invoices(self, client, app):
        """Activity feed should include recent orders, payments, and invoices."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            order = CustomerOrder(
                coid="CO-001", cid="C-001", created_by="USR-ADMIN01",
                order_date=date.today(), status="Completed",
                total_amount=Decimal("500"),
            )
            detail = CustomerOrderDetail(
                codid="COD-001", coid="CO-001", skuid="SKU-1",
                quantity=10, amount=Decimal("500"),
            )
            slip = PackingSlip(
                pslip_id="PS-001", coid="CO-001",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d = PackingSlipDetail(
                psd_id="PSD-001", pslip_id="PS-001",
                skuid="SKU-1", packed_qty=10,
            )
            inv = CustomerInvoice(
                cinv_id="INV-001", pslip_id="PS-001",
                created_by="USR-ADMIN01", invoice_date=date.today(),
                status="Paid", total_amount=Decimal("500"),
            )
            inv_d = CustomerInvDetail(
                cdetail_id="CD-001", cinv_id="INV-001",
                skuid="SKU-1", ordered_qty=10, delivered_qty=10,
                sale_price=Decimal("50"), amount=Decimal("500"),
            )
            pay = Payment(
                payment_id="PAY-001", cinv_id="INV-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("500"), method="Cash",
            )
            db.session.add_all([order, detail, slip, slip_d, inv, inv_d, pay])
            db.session.commit()

        response = client.get("/api/internal-portal/overview")

        assert response.status_code == 200
        feed = response.get_json()["activityFeed"]
        assert len(feed) >= 3
        titles = {a["title"] for a in feed}
        assert "Order placed" in titles
        assert "Payment in" in titles
        # Invoice could be "Invoice raised" or "Invoice overdue" depending on ACP
        assert any("Invoice" in t for t in titles)
