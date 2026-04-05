from datetime import date
from decimal import Decimal

from app import db
from app.auth import issue_token
from app.models.product import Product
from app.models.sku import SKU
from app.models.user import User
from app.models.vendor import Vendor, VendorProduct
from app.models.vendor_order import VendorOrder, VendorOrderDetail


def _create_admin():
    admin = User(
        uid="USR-ADMIN01",
        full_name="Metro Business Owner",
        email="owner@metrohardware.com",
        role=User.ROLE_ADMIN,
        is_active=True,
    )
    admin.set_password("password123")
    return admin


def test_vendor_list_returns_vendors_with_contact_location_and_products(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)

        vendor_with_products = Vendor(
            vid="1",
            vendor_name="Amul Engineering",
            vendor_prefix="AM",
            lead_time=4,
            location="Rajkot",
            contact="9428037277",
            email="sales@amul.example",
        )
        vendor_without_products = Vendor(
            vid="2",
            vendor_name="Khedut Enterprises",
            vendor_prefix="KE",
            location="Rajkot",
            contact="9909026268",
            email="hello@khedut.example",
        )
        product_one = Product(pid="10", pname="SS Step Nipple", category="Pipe Fittings")
        product_two = Product(pid="11", pname="GI Step Nipple", category="Pipe Fittings")
        db.session.add_all(
            [
                vendor_with_products,
                vendor_without_products,
                product_one,
                product_two,
                VendorProduct(vpid="VP-1", vid="1", pid="10"),
                VendorProduct(vpid="VP-2", vid="1", pid="11"),
            ]
        )
        db.session.commit()
        token = issue_token(admin)

    response = client.get(
        "/api/vendors",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["vendors"]) == 2

    first_vendor = next(vendor for vendor in payload["vendors"] if vendor["id"] == "1")
    assert first_vendor["name"] == "Amul Engineering"
    assert first_vendor["prefix"] == "AM"
    assert first_vendor["leadTime"] == 4
    assert first_vendor["location"] == "Rajkot"
    assert first_vendor["contact"]["phone"] == "9428037277"
    assert first_vendor["contact"]["email"] == "sales@amul.example"
    assert first_vendor["parts"] == ["GI Step Nipple", "SS Step Nipple"]
    assert first_vendor["partCount"] == 2

    second_vendor = next(vendor for vendor in payload["vendors"] if vendor["id"] == "2")
    assert second_vendor["parts"] == []
    assert second_vendor["products"] == []
    assert second_vendor["partCount"] == 0


def test_vendor_detail_returns_single_vendor_with_products(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)

        vendor = Vendor(
            vid="1",
            vendor_name="Shyam Industries",
            vendor_prefix="SI",
            lead_time=6,
            location="Ribda, Rajkot",
            contact="9426460656",
            email="shyam@example.com",
        )
        db.session.add_all(
            [
                vendor,
                Product(pid="1", pname="Butterfly Valve", category="Pipe Fittings"),
                Product(pid="2", pname="Sprinkler Clamp", category="Pipe Fittings"),
                VendorProduct(vpid="VP-1", vid="1", pid="1"),
                VendorProduct(vpid="VP-2", vid="1", pid="2"),
            ]
        )
        db.session.commit()
        token = issue_token(admin)

    response = client.get(
        "/api/vendors/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()["vendor"]
    assert payload["id"] == "1"
    assert payload["name"] == "Shyam Industries"
    assert payload["prefix"] == "SI"
    assert payload["leadTime"] == 6
    assert payload["location"] == "Ribda, Rajkot"
    assert payload["contact"]["phone"] == "9426460656"
    assert payload["products"] == [
        {"id": "1", "name": "Butterfly Valve", "category": "Pipe Fittings"},
        {"id": "2", "name": "Sprinkler Clamp", "category": "Pipe Fittings"},
    ]
    assert payload["parts"] == ["Butterfly Valve", "Sprinkler Clamp"]


def test_vendor_endpoints_require_admin_role(client, app):
    with app.app_context():
        customer = User(
            uid="USR-CUST01",
            full_name="Sample Customer",
            email="customer@example.com",
            role=User.ROLE_CUSTOMER,
            is_active=True,
        )
        customer.set_password("password123")
        db.session.add(customer)
        db.session.commit()
        token = issue_token(customer)

    response = client.get(
        "/api/vendors",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "You do not have access to this resource."


def test_vendor_compare_catalog_returns_products_sizes_and_vendor_prices(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)

        vendor_one = Vendor(
            vid="1",
            vendor_name="Amul Engineering",
            lead_time=5,
            location="Rajkot",
            contact="9428037277",
            email="sales@amul.example",
        )
        vendor_two = Vendor(
            vid="2",
            vendor_name="Khedut Enterprises",
            lead_time=3,
            location="Rajkot",
            contact="9909026268",
            email="hello@khedut.example",
        )
        product_with_sizes = Product(pid="10", pname="SS Step Nipple", category="Pipe Fittings")
        product_without_sizes = Product(pid="11", pname="GI Step Nipple", category="Pipe Fittings")
        db.session.add_all(
            [
                vendor_one,
                vendor_two,
                product_with_sizes,
                product_without_sizes,
                VendorProduct(vpid="VP-1", vid="1", pid="10"),
                VendorProduct(vpid="VP-2", vid="2", pid="10"),
            ]
        )
        db.session.add_all(
            [
                SKU(
                    skuid="SKU-1",
                    vpid="VP-1",
                    current_buy_rate=Decimal("40.00"),
                    specs={"spec1": '1" x 0.75" x 7"', "spec2": "63 mm"},
                ),
                SKU(
                    skuid="SKU-2",
                    vpid="VP-1",
                    current_buy_rate=Decimal("38.00"),
                    specs={"spec1": '1" x 0.75" x 7"', "spec2": "63 mm"},
                ),
                SKU(
                    skuid="SKU-3",
                    vpid="VP-2",
                    current_buy_rate=Decimal("35.00"),
                    specs={"spec1": '1" x 0.75" x 7"', "spec2": "63 mm"},
                ),
            ]
        )
        db.session.commit()
        token = issue_token(admin)

    response = client.get(
        "/api/vendors/catalog/compare",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["parts"]) == 2

    compare_part = next(part for part in payload["parts"] if part["id"] == "10")
    assert compare_part["name"] == "SS Step Nipple"
    assert len(compare_part["sizes"]) == 1
    assert compare_part["sizes"][0]["key"] == '63 mm\n1" x 0.75" x 7"'
    assert compare_part["sizes"][0]["size"] == "63 mm"
    assert compare_part["sizes"][0]["spec"] == '1" x 0.75" x 7"'
    assert compare_part["sizes"][0]["suppliers"] == [
        {
            "vendorId": "2",
            "skuId": "SKU-3",
            "price": 35.0,
            "currentBuy": 35.0,
            "unitMeasurementBuy": None,
            "lotSize": None,
            "leadTime": 3,
            "vendor": {"id": "2", "name": "Khedut Enterprises", "location": "Rajkot", "leadTime": 3},
        },
        {
            "vendorId": "1",
            "skuId": "SKU-2",
            "price": 38.0,
            "currentBuy": 38.0,
            "unitMeasurementBuy": None,
            "lotSize": None,
            "leadTime": 5,
            "vendor": {"id": "1", "name": "Amul Engineering", "location": "Rajkot", "leadTime": 5},
        },
    ]

    empty_part = next(part for part in payload["parts"] if part["id"] == "11")
    assert empty_part["sizes"] == []


def test_vendor_procurement_creation_persists_order_and_appears_in_history(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)

        vendor = Vendor(
            vid="1",
            vendor_name="Amul Engineering",
            lead_time=4,
            location="Rajkot",
            contact="9428037277",
            email="sales@amul.example",
        )
        product = Product(pid="10", pname="Borcap", category="Pipe Fittings")
        vendor_product = VendorProduct(vpid="VP-1", vid="1", pid="10")
        sku = SKU(
            skuid="SKU-1",
            vpid="VP-1",
            current_buy_rate=Decimal("12.50"),
            unit_measurement_buy=4,
            lot_size_buy=3,
            specs={"spec1": '12mm x 45 mm', "spec2": '1.5"'},
        )
        db.session.add_all([vendor, product, vendor_product, sku])
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/vendors/procurements",
        headers={"Authorization": f"Bearer {token}"},
        json={"skuId": "SKU-1", "vendorId": "1", "lotCount": 2},
    )

    assert response.status_code == 201
    created = response.get_json()["procurement"]
    assert created["partName"] == "Borcap"
    assert created["specification"] == '1.5" · 12mm x 45 mm'
    assert created["vendor"]["name"] == "Amul Engineering"
    assert created["currentBuy"] == 12.5
    assert created["unitMeasurementBuy"] == 4
    assert created["lotSize"] == 3
    assert created["lotCount"] == 2
    assert created["orderedQty"] == 24
    assert created["totalCost"] == 300.0
    assert created["status"] == "pending"

    with app.app_context():
        order = VendorOrder.query.one()
        detail = VendorOrderDetail.query.one()
        assert order.vid == "1"
        assert order.created_by == "USR-ADMIN01"
        assert order.status == "Confirmed"
        assert order.total_amount == Decimal("300.00")
        assert detail.skuid == "SKU-1"
        assert detail.ordered_qty == 24
        assert detail.agree_price == Decimal("12.50")
        assert detail.amount == Decimal("300.00")

    history_response = client.get(
        "/api/vendors/procurements",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert history_response.status_code == 200
    history = history_response.get_json()["procurements"]
    assert len(history) == 1
    assert history[0]["id"] == created["id"]
    assert history[0]["orderedQty"] == 24
    assert history[0]["lotCount"] == 2


def test_vendor_procurement_can_be_marked_received(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)

        vendor = Vendor(
            vid="1",
            vendor_name="Amul Engineering",
            lead_time=4,
            location="Rajkot",
            contact="9428037277",
            email="sales@amul.example",
        )
        product = Product(pid="10", pname="Borcap", category="Pipe Fittings")
        vendor_product = VendorProduct(vpid="VP-1", vid="1", pid="10")
        sku = SKU(
            skuid="SKU-1",
            vpid="VP-1",
            current_buy_rate=Decimal("12.50"),
            unit_measurement_buy=5,
            lot_size_buy=2,
            specs={"spec1": '12mm x 45 mm', "spec2": '2"'},
            stock_qty=7,
        )
        order = VendorOrder(
            void="VO-TEST001",
            vid="1",
            created_by="USR-ADMIN01",
            order_date=date.today(),
            status="Confirmed",
            total_amount=Decimal("125.00"),
        )
        detail = VendorOrderDetail(
            vo_detail_id="VOD-TEST01",
            void="VO-TEST001",
            skuid="SKU-1",
            ordered_qty=10,
            agree_price=Decimal("12.50"),
            amount=Decimal("125.00"),
        )
        db.session.add_all([vendor, product, vendor_product, sku, order, detail])
        db.session.commit()
        token = issue_token(admin)

    response = client.patch(
        "/api/vendors/procurements/VO-TEST001/receive",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()["procurement"]
    assert payload["id"] == "VO-TEST001"
    assert payload["status"] == "received"

    with app.app_context():
        order = VendorOrder.query.filter_by(void="VO-TEST001").first()
        sku = SKU.query.filter_by(skuid="SKU-1").first()
        assert order is not None
        assert sku is not None
        assert order.status == "Completed"
        assert sku.stock_qty == 17

    repeat_response = client.patch(
        "/api/vendors/procurements/VO-TEST001/receive",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert repeat_response.status_code == 200

    with app.app_context():
        sku = SKU.query.filter_by(skuid="SKU-1").first()
        assert sku is not None
        assert sku.stock_qty == 17
