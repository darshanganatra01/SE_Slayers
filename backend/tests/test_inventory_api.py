from decimal import Decimal

from app import db
from app.auth import issue_token
from app.models.product import Product
from app.models.sku import SKU
from app.models.user import User
from app.models.vendor import Vendor, VendorProduct


def test_inventory_overview_returns_joined_parts_and_statuses(client, app):
    with app.app_context():
        admin = User(
            uid="USR-ADMIN01",
            full_name="Metro Business Owner",
            email="owner@metrohardware.com",
            role=User.ROLE_ADMIN,
            is_active=True,
        )
        admin.set_password("password123")
        db.session.add(admin)

        vendor = Vendor(
            vid="1",
            vendor_name="Amul Engineering",
            vendor_prefix="AM",
        )
        product = Product(
            pid="1",
            pname="SS Step Nipple",
            category="Pipe Fittings",
        )
        product_without_variants = Product(
            pid="2",
            pname="SS Reduce Nipple",
            category="Pipe Fittings",
        )
        vendor_product = VendorProduct(
            vpid="10",
            vid="1",
            pid="1",
        )
        db.session.add_all([vendor, product, product_without_variants, vendor_product])

        db.session.add_all(
            [
                SKU(
                    skuid="SKU-1",
                    vpid="10",
                    current_sell_rate=Decimal("30.00"),
                    stock_qty=10,
                    threshold=5,
                    specs={"spec1": "Clamp 2.5mm", "spec2": "63 mm"},
                ),
                SKU(
                    skuid="SKU-2",
                    vpid="10",
                    current_sell_rate=Decimal("45.00"),
                    stock_qty=2,
                    threshold=5,
                    specs={"spec1": "Clamp SS", "spec2": "90 mm"},
                ),
                SKU(
                    skuid="SKU-3",
                    vpid="10",
                    current_sell_rate=Decimal("50.00"),
                    stock_qty=0,
                    threshold=5,
                    specs={"spec1": "Clamp SS", "spec2": "110 mm"},
                ),
            ]
        )
        db.session.commit()
        token = issue_token(admin)

    response = client.get(
        "/api/inventory/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["summary"]["totalParts"] == 3
    assert payload["summary"]["inStockCount"] == 1
    assert payload["summary"]["lowOnlyCount"] == 1
    assert payload["summary"]["outOfStockCount"] == 1
    assert len(payload["portfolioProducts"]) == 2

    first_part = payload["parts"][0]
    assert first_part["name"] == "SS Step Nipple"
    assert first_part["size"] == "63 mm"
    assert first_part["spec"] == "Clamp 2.5mm"
    assert first_part["status"] == "instock"

    empty_portfolio_entry = next(item for item in payload["portfolioProducts"] if item["key"] == "2")
    assert empty_portfolio_entry["name"] == "SS Reduce Nipple"
    assert empty_portfolio_entry["sizes"] == []


def test_inventory_overview_requires_admin_role(client, app):
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
        "/api/inventory/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "You do not have access to this resource."


def test_inventory_portfolio_keeps_distinct_full_spec_combinations(client, app):
    with app.app_context():
        admin = User(
            uid="USR-ADMIN02",
            full_name="Metro Business Owner",
            email="owner2@metrohardware.com",
            role=User.ROLE_ADMIN,
            is_active=True,
        )
        admin.set_password("password123")
        db.session.add(admin)

        vendor = Vendor(
            vid="1",
            vendor_name="Amul Engineering",
            vendor_prefix="AM",
        )
        product = Product(
            pid="1",
            pname="Borcap",
            category="Pipe Fittings",
        )
        vendor_product = VendorProduct(vpid="10", vid="1", pid="1")
        db.session.add_all([vendor, product, vendor_product])

        db.session.add_all(
            [
                SKU(
                    skuid="SKU-1",
                    vpid="10",
                    current_sell_rate=Decimal("30.00"),
                    stock_qty=10,
                    threshold=5,
                    specs={"spec1": '1.5"', "spec2": "58 to 62 mm", "spec3": "12mm x 45 mm"},
                ),
                SKU(
                    skuid="SKU-2",
                    vpid="10",
                    current_sell_rate=Decimal("45.00"),
                    stock_qty=2,
                    threshold=5,
                    specs={"spec1": '2"', "spec2": "70 to 74 mm", "spec3": "12mm x 45 mm"},
                ),
            ]
        )
        db.session.commit()
        token = issue_token(admin)

    response = client.get(
        "/api/inventory/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    borcap = next(item for item in payload["portfolioProducts"] if item["key"] == "1")
    assert borcap["sizes"] == [
        {"key": '12mm x 45 mm\n1.5" · 58 to 62 mm', "label": "12mm x 45 mm", "detail": '1.5" · 58 to 62 mm', "status": "ok"},
        {"key": '12mm x 45 mm\n2" · 70 to 74 mm', "label": "12mm x 45 mm", "detail": '2" · 70 to 74 mm', "status": "low"},
    ]

    borcap_details = payload["portfolioDetails"]["1"]["rows"]
    assert [row["key"] for row in borcap_details] == [
        '12mm x 45 mm\n1.5" · 58 to 62 mm',
        '12mm x 45 mm\n2" · 70 to 74 mm',
    ]
