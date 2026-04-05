"""Tests for Internal Portal – Customers page APIs.

Covers:
  GET  /api/internal-portal/customers
  POST /api/internal-portal/collect-payment
"""

from datetime import date
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
        uid=uid,
        full_name=name,
        email=email,
        role=User.ROLE_CUSTOMER,
        is_active=True,
    )
    user.set_password("password123")
    return user


def _customer(cid="C-001", uid="USR-CUST01", name="Raj Hardware", acp=15,
              location="Rajkot", contact="9999999999", email="raj@example.com"):
    return Customer(
        cid=cid,
        uid=uid,
        customer_name=name,
        acp=acp,
        location=location,
        contact=contact,
        email=email,
    )


def _full_product_chain(skuid="SKU-1", sell_rate="50.00", stock=100, threshold=10):
    """Create Vendor -> Product -> VendorProduct -> SKU chain."""
    vendor = Vendor(vid="V-1", vendor_name="Amul Engineering", vendor_prefix="AM")
    product = Product(pid="P-1", pname="SS Step Nipple", category="Pipe Fittings")
    vp = VendorProduct(vpid="VP-1", vid="V-1", pid="P-1")
    sku = SKU(
        skuid=skuid,
        vpid="VP-1",
        current_sell_rate=Decimal(sell_rate),
        stock_qty=stock,
        threshold=threshold,
        specs={"spec1": "63 mm", "spec2": "Clamp 2.5mm"},
    )
    return vendor, product, vp, sku


def _order_with_invoice(cid, coid, skuid, qty, sale_price, packed_qty, admin_uid,
                        inv_status="Unpaid", slip_status="Shipped"):
    """Create a full order -> packing slip -> invoice chain."""
    order = CustomerOrder(
        coid=coid, cid=cid, created_by=admin_uid,
        order_date=date.today(), status="Completed",
        priority="High", total_amount=Decimal(str(qty * float(sale_price))),
    )
    detail = CustomerOrderDetail(
        codid=f"COD-{coid}", coid=coid, skuid=skuid,
        quantity=qty, amount=Decimal(str(qty * float(sale_price))),
    )
    slip = PackingSlip(
        pslip_id=f"PS-{coid}", coid=coid,
        packed_by=admin_uid, packed_date=date.today(), status=slip_status,
    )
    slip_detail = PackingSlipDetail(
        psd_id=f"PSD-{coid}", pslip_id=f"PS-{coid}",
        skuid=skuid, packed_qty=packed_qty,
    )
    invoice = CustomerInvoice(
        cinv_id=f"INV-{coid}", pslip_id=f"PS-{coid}",
        created_by=admin_uid, invoice_date=date.today(),
        status=inv_status, total_amount=Decimal(str(packed_qty * float(sale_price))),
    )
    inv_detail = CustomerInvDetail(
        cdetail_id=f"CD-{coid}", cinv_id=f"INV-{coid}",
        skuid=skuid, ordered_qty=qty, delivered_qty=packed_qty,
        sale_price=Decimal(sale_price), amount=Decimal(str(packed_qty * float(sale_price))),
    )
    return order, detail, slip, slip_detail, invoice, inv_detail


# ═══════════════════════════════════════════════════════════════════
# GET /api/internal-portal/customers
# ═══════════════════════════════════════════════════════════════════

class TestCustomersListEndpoint:
    """Tests for the customer listing endpoint."""

    def test_returns_empty_list_when_no_customers_exist(self, client, app):
        """Verify endpoint returns an empty list when there are no customers."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload == []

    def test_returns_customer_basic_fields(self, client, app):
        """Verify all basic customer fields are returned correctly."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            db.session.add_all([admin, cust_user, cust])
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 1

        c = payload[0]
        assert c["id"] == "C-001"
        assert c["name"] == "Raj Hardware"
        assert c["phone"] == "9999999999"
        assert c["email"] == "raj@example.com"
        assert c["loc"] == "Rajkot"
        assert c["acp"] == 15
        assert c["totalOrders"] == 0
        assert c["totalValue"] == 0
        assert c["pending"] == 0
        assert c["orders"] == []
        assert c["invoices"] == []
        assert c["payHistory"] == []

    def test_acp_maps_to_correct_customer_type(self, client, app):
        """ACP 1 -> Platinum, ACP 2 -> Gold, ACP 3 -> Silver, None -> Platinum."""
        with app.app_context():
            admin = _admin()
            db.session.add(admin)
            users_custs = []
            for idx, (acp_val, expected_type) in enumerate([
                (1, "Platinum"), (2, "Gold"), (3, "Silver"), (None, "Platinum")
            ]):
                uid = f"USR-C{idx}"
                u = _customer_user(uid=uid, email=f"c{idx}@test.com", name=f"Cust{idx}")
                c = _customer(cid=f"C-{idx}", uid=uid, name=f"Cust{idx}", acp=acp_val)
                users_custs.extend([u, c])
            db.session.add_all(users_custs)
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 4
        type_map = {c["id"]: c["type"] for c in payload}
        assert type_map["C-0"] == "Platinum"
        assert type_map["C-1"] == "Gold"
        assert type_map["C-2"] == "Silver"
        assert type_map["C-3"] == "Platinum"

    def test_customer_with_orders_shows_correct_totals(self, client, app):
        """Verify totalOrders and totalValue aggregate correctly across orders."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            # Two orders for same customer
            o1 = CustomerOrder(
                coid="CO-001", cid="C-001", created_by="USR-ADMIN01",
                order_date=date.today(), status="Confirmed",
                priority="High", total_amount=Decimal("500.00"),
            )
            d1 = CustomerOrderDetail(
                codid="COD-001", coid="CO-001", skuid="SKU-1",
                quantity=10, amount=Decimal("500.00"),
            )
            o2 = CustomerOrder(
                coid="CO-002", cid="C-001", created_by="USR-ADMIN01",
                order_date=date.today(), status="Confirmed",
                priority="High", total_amount=Decimal("250.00"),
            )
            d2 = CustomerOrderDetail(
                codid="COD-002", coid="CO-002", skuid="SKU-1",
                quantity=5, amount=Decimal("250.00"),
            )
            db.session.add_all([o1, d1, o2, d2])
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        c = response.get_json()[0]
        assert c["totalOrders"] == 2
        assert c["totalValue"] == 750.0

    def test_customer_invoices_and_pending_amounts(self, client, app):
        """Verify invoices list and pending amount when partially paid."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            items = _order_with_invoice("C-001", "CO-001", "SKU-1", 10, "50.00", 10, "USR-ADMIN01")
            db.session.add_all(items)

            # Partial payment: pay 200 out of 500
            payment = Payment(
                payment_id="PAY-001", cinv_id="INV-CO-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("200.00"), method="Cash",
            )
            db.session.add(payment)
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        c = response.get_json()[0]
        assert c["pending"] == 300.0  # 500 - 200
        assert len(c["invoices"]) == 1
        assert c["invoices"][0]["id"] == "INV-CO-001"
        assert c["invoices"][0]["amount"] == 500.0
        assert c["invoices"][0]["status"] == "pending"

    def test_fully_paid_invoice_shows_paid_status(self, client, app):
        """Invoice that is fully paid should have status='paid' and pending=0."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            items = _order_with_invoice("C-001", "CO-001", "SKU-1", 10, "50.00", 10, "USR-ADMIN01")
            db.session.add_all(items)

            payment = Payment(
                payment_id="PAY-001", cinv_id="INV-CO-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("500.00"), method="Bank Transfer",
            )
            db.session.add(payment)
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        c = response.get_json()[0]
        assert c["pending"] == 0
        assert c["invoices"][0]["status"] == "paid"

    def test_payment_history_entries_returned(self, client, app):
        """Verify payHistory includes all payment records for customer invoices."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            items = _order_with_invoice("C-001", "CO-001", "SKU-1", 10, "50.00", 10, "USR-ADMIN01")
            db.session.add_all(items)

            p1 = Payment(
                payment_id="PAY-001", cinv_id="INV-CO-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("200.00"), method="Cash", notes="First installment",
            )
            p2 = Payment(
                payment_id="PAY-002", cinv_id="INV-CO-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("300.00"), method="UPI", notes="Final payment",
            )
            db.session.add_all([p1, p2])
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        c = response.get_json()[0]
        assert len(c["payHistory"]) == 2
        amounts = sorted([p["amount"] for p in c["payHistory"]])
        assert amounts == [200.0, 300.0]

    def test_multiple_customers_returned_independently(self, client, app):
        """Ensure multiple customers are returned as separate entries."""
        with app.app_context():
            admin = _admin()
            u1 = _customer_user(uid="USR-C1", email="cust1@test.com", name="Customer One")
            u2 = _customer_user(uid="USR-C2", email="cust2@test.com", name="Customer Two")
            c1 = _customer(cid="C-001", uid="USR-C1", name="Customer One", acp=1)
            c2 = _customer(cid="C-002", uid="USR-C2", name="Customer Two", acp=3)
            db.session.add_all([admin, u1, u2, c1, c2])
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 2
        names = {c["name"] for c in payload}
        assert names == {"Customer One", "Customer Two"}

    def test_customer_order_paid_status_derived_from_invoice_payments(self, client, app):
        """Order 'paid' field should be 'Paid' when all invoices are fully paid."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            items = _order_with_invoice("C-001", "CO-001", "SKU-1", 5, "50.00", 5, "USR-ADMIN01")
            db.session.add_all(items)

            payment = Payment(
                payment_id="PAY-001", cinv_id="INV-CO-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("250.00"), method="Cash",
            )
            db.session.add(payment)
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        order_entry = response.get_json()[0]["orders"][0]
        assert order_entry["paid"] == "Paid"

    def test_customer_with_no_contact_shows_empty_string(self, client, app):
        """Customers with None contact/email should return empty strings."""
        with app.app_context():
            admin = _admin()
            u = _customer_user()
            c = _customer(contact=None, email=None, location=None)
            db.session.add_all([admin, u, c])
            db.session.commit()

        response = client.get("/api/internal-portal/customers")

        assert response.status_code == 200
        cust = response.get_json()[0]
        assert cust["phone"] == ""
        assert cust["email"] == ""
        assert cust["loc"] == ""


# ═══════════════════════════════════════════════════════════════════
# POST /api/internal-portal/collect-payment
# ═══════════════════════════════════════════════════════════════════

class TestCollectPaymentEndpoint:
    """Tests for payment collection via FIFO allocation."""

    def test_collect_payment_distributes_fifo_across_invoices(self, client, app):
        """Payment should be applied to oldest unpaid invoice first (FIFO)."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            # Create two invoices: CO-001 (200) and CO-002 (300)
            items1 = _order_with_invoice("C-001", "CO-001", "SKU-1", 4, "50.00", 4, "USR-ADMIN01")
            # Need a second SKU or order with different coid
            o2 = CustomerOrder(
                coid="CO-002", cid="C-001", created_by="USR-ADMIN01",
                order_date=date.today(), status="Completed",
                priority="High", total_amount=Decimal("300.00"),
            )
            od2 = CustomerOrderDetail(
                codid="COD-002", coid="CO-002", skuid="SKU-1",
                quantity=6, amount=Decimal("300.00"),
            )
            slip2 = PackingSlip(
                pslip_id="PS-CO-002", coid="CO-002",
                packed_by="USR-ADMIN01", packed_date=date.today(), status="Shipped",
            )
            slip_d2 = PackingSlipDetail(
                psd_id="PSD-CO-002", pslip_id="PS-CO-002",
                skuid="SKU-1", packed_qty=6,
            )
            inv2 = CustomerInvoice(
                cinv_id="INV-CO-002", pslip_id="PS-CO-002",
                created_by="USR-ADMIN01", invoice_date=date.today(),
                status="Unpaid", total_amount=Decimal("300.00"),
            )
            inv_d2 = CustomerInvDetail(
                cdetail_id="CD-CO-002", cinv_id="INV-CO-002",
                skuid="SKU-1", ordered_qty=6, delivered_qty=6,
                sale_price=Decimal("50.00"), amount=Decimal("300.00"),
            )
            db.session.add_all(list(items1) + [o2, od2, slip2, slip_d2, inv2, inv_d2])
            db.session.commit()

        # Collect 350 -> should fully pay CO-001 (200) and partially pay CO-002 (150 of 300)
        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"cid": "C-001", "amount": 350},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["collected"] == 350
        assert len(payload["allocations"]) == 2

    def test_collect_payment_rejects_zero_amount(self, client, app):
        """Payment with zero or negative amount should be rejected."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            db.session.add_all([admin, cust_user, cust])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"cid": "C-001", "amount": 0},
        )

        assert response.status_code == 400
        assert "Valid Customer ID and amount" in response.get_json()["message"]

    def test_collect_payment_rejects_negative_amount(self, client, app):
        """Payment with negative amount should be rejected."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            db.session.add_all([admin, cust_user, cust])
            db.session.commit()

        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"cid": "C-001", "amount": -100},
        )

        assert response.status_code == 400

    def test_collect_payment_for_nonexistent_customer_returns_404(self, client, app):
        """Attempting to collect payment for a non-existent customer returns 404."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"cid": "C-NONEXIST", "amount": 100},
        )

        assert response.status_code == 404
        assert "Customer not found" in response.get_json()["message"]

    def test_collect_payment_missing_cid_returns_400(self, client, app):
        """Request without cid should return 400."""
        with app.app_context():
            db.session.add(_admin())
            db.session.commit()

        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"amount": 100},
        )

        assert response.status_code == 400

    def test_collect_payment_excess_amount_collects_only_outstanding(self, client, app):
        """When payment exceeds total outstanding, only the outstanding amount is collected."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            items = _order_with_invoice("C-001", "CO-001", "SKU-1", 4, "50.00", 4, "USR-ADMIN01")
            db.session.add_all(items)
            db.session.commit()

        # Invoice total is 200, pay 500
        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"cid": "C-001", "amount": 500},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["collected"] == 200  # Only 200 unpaid

    def test_collect_payment_when_all_invoices_already_paid(self, client, app):
        """Collecting payment when nothing is outstanding should collect 0."""
        with app.app_context():
            admin = _admin()
            cust_user = _customer_user()
            cust = _customer()
            vendor, product, vp, sku = _full_product_chain()
            db.session.add_all([admin, cust_user, cust, vendor, product, vp, sku])

            items = _order_with_invoice("C-001", "CO-001", "SKU-1", 4, "50.00", 4, "USR-ADMIN01")
            db.session.add_all(items)

            # Fully paid
            payment = Payment(
                payment_id="PAY-001", cinv_id="INV-CO-001",
                recorded_by="USR-ADMIN01", payment_date=date.today(),
                amount=Decimal("200.00"), method="Cash",
            )
            db.session.add(payment)
            db.session.commit()

        response = client.post(
            "/api/internal-portal/collect-payment",
            json={"cid": "C-001", "amount": 100},
        )

        assert response.status_code == 200
        assert response.get_json()["collected"] == 0
