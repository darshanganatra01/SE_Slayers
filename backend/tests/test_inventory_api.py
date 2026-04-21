from decimal import Decimal

from app import db
from app.auth import issue_token
from app.models.product import Product
from app.models.sku import SKU
from app.models.user import User
from app.models.vendor import Vendor, VendorProduct


def _create_admin(uid="USR-ADMIN01", email="owner@metrohardware.com"):
    admin = User(
        uid=uid,
        full_name="Metro Business Owner",
        email=email,
        role=User.ROLE_ADMIN,
        is_active=True,
    )
    admin.set_password("password123")
    return admin


def test_inventory_overview_returns_joined_parts_and_statuses(client, app):
    with app.app_context():
        admin = _create_admin()
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
        admin = _create_admin(uid="USR-ADMIN02", email="owner2@metrohardware.com")
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


def test_inventory_part_creation_persists_product_vendor_links_and_skus(client, app):
    with app.app_context():
        admin = _create_admin()
        vendor_one = Vendor(vid="1", vendor_name="Amul Engineering", vendor_prefix="AE")
        vendor_two = Vendor(vid="2", vendor_name="Khedut Enterprises", vendor_prefix="KE")
        db.session.add_all([admin, vendor_one, vendor_two])
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/inventory/parts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Borcap",
            "category": "Pipe Fittings",
            "vendorIds": ["1", "2"],
            "unitMeasurementBuy": 6,
            "lotSizeBuy": 3,
            "specs": [
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 24,
                    "threshold": 5,
                    "sellPrice": "64.50",
                    "vendorPrices": [
                        {"vendorId": "1", "unitBuyPrice": "42.00"},
                        {"vendorId": "2", "unitBuyPrice": "40.50"},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.get_json()["product"]
    assert payload == {
        "id": "1",
        "name": "Borcap",
        "category": "Pipe Fittings",
        "image": None,
        "vendorIds": ["1", "2"],
        "specCount": 1,
    }

    with app.app_context():
        product = Product.query.filter_by(pid="1").first()
        assert product is not None
        assert product.pname == "Borcap"
        assert product.category == "Pipe Fittings"

        vendor_products = VendorProduct.query.filter_by(pid="1").order_by(VendorProduct.vid.asc()).all()
        assert [vendor_product.vid for vendor_product in vendor_products] == ["1", "2"]

        sku_one = (
            db.session.query(SKU)
            .join(VendorProduct, VendorProduct.vpid == SKU.vpid)
            .filter(VendorProduct.pid == "1", VendorProduct.vid == "1")
            .one()
        )
        sku_two = (
            db.session.query(SKU)
            .join(VendorProduct, VendorProduct.vpid == SKU.vpid)
            .filter(VendorProduct.pid == "1", VendorProduct.vid == "2")
            .one()
        )

        assert sku_one.unit_measurement_buy == 6
        assert sku_one.lot_size_buy == 3
        assert sku_one.current_buy_rate == Decimal("42.00")
        assert sku_one.current_sell_rate == Decimal("64.50")
        assert sku_one.stock_qty == 24
        assert sku_one.threshold == 5
        assert sku_one.specs == {"spec1": "12mm x 45 mm"}

        assert sku_two.unit_measurement_buy == 6
        assert sku_two.lot_size_buy == 3
        assert sku_two.current_buy_rate == Decimal("40.50")
        assert sku_two.current_sell_rate is None
        assert sku_two.stock_qty == 0
        assert sku_two.threshold == 0
        assert sku_two.specs == {"spec1": "12mm x 45 mm"}


def test_inventory_part_creation_requires_product_name(client, app):
    with app.app_context():
        admin = _create_admin()
        vendor = Vendor(vid="1", vendor_name="Amul Engineering", vendor_prefix="AE")
        db.session.add_all([admin, vendor])
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/inventory/parts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "   ",
            "category": "Pipe Fittings",
            "vendorIds": ["1"],
            "unitMeasurementBuy": 6,
            "lotSizeBuy": 3,
            "specs": [
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 24,
                    "threshold": 5,
                    "sellPrice": "64.50",
                    "vendorPrices": [{"vendorId": "1", "unitBuyPrice": "42.00"}],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Product name is required."


def test_inventory_part_creation_requires_at_least_one_vendor(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/inventory/parts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Borcap",
            "category": "Pipe Fittings",
            "vendorIds": [],
            "unitMeasurementBuy": 6,
            "lotSizeBuy": 3,
            "specs": [
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 24,
                    "threshold": 5,
                    "sellPrice": "64.50",
                    "vendorPrices": [],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Select at least one vendor so the new specifications can be stored."


def test_inventory_part_creation_rejects_duplicate_specifications(client, app):
    with app.app_context():
        admin = _create_admin()
        vendor = Vendor(vid="1", vendor_name="Amul Engineering", vendor_prefix="AE")
        db.session.add_all([admin, vendor])
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/inventory/parts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Borcap",
            "category": "Pipe Fittings",
            "vendorIds": ["1"],
            "unitMeasurementBuy": 6,
            "lotSizeBuy": 3,
            "specs": [
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 24,
                    "threshold": 5,
                    "sellPrice": "64.50",
                    "vendorPrices": [{"vendorId": "1", "unitBuyPrice": "42.00"}],
                },
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 12,
                    "threshold": 3,
                    "sellPrice": "61.00",
                    "vendorPrices": [{"vendorId": "1", "unitBuyPrice": "40.00"}],
                },
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Duplicate specification found: 12mm x 45 mm."


def test_inventory_part_creation_requires_vendor_prices_for_all_selected_vendors(client, app):
    with app.app_context():
        admin = _create_admin()
        vendor_one = Vendor(vid="1", vendor_name="Amul Engineering", vendor_prefix="AE")
        vendor_two = Vendor(vid="2", vendor_name="Khedut Enterprises", vendor_prefix="KE")
        db.session.add_all([admin, vendor_one, vendor_two])
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/inventory/parts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Borcap",
            "category": "Pipe Fittings",
            "vendorIds": ["1", "2"],
            "unitMeasurementBuy": 6,
            "lotSizeBuy": 3,
            "specs": [
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 24,
                    "threshold": 5,
                    "sellPrice": "64.50",
                    "vendorPrices": [{"vendorId": "1", "unitBuyPrice": "42.00"}],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Enter unit buy prices for every selected vendor for 12mm x 45 mm."


def test_inventory_part_creation_rejects_unknown_vendor_selection(client, app):
    with app.app_context():
        admin = _create_admin()
        db.session.add(admin)
        db.session.commit()
        token = issue_token(admin)

    response = client.post(
        "/api/inventory/parts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Borcap",
            "category": "Pipe Fittings",
            "vendorIds": ["999"],
            "unitMeasurementBuy": 6,
            "lotSizeBuy": 3,
            "specs": [
                {
                    "label": "12mm x 45 mm",
                    "stockQty": 24,
                    "threshold": 5,
                    "sellPrice": "64.50",
                    "vendorPrices": [{"vendorId": "999", "unitBuyPrice": "42.00"}],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Unknown vendor selection: 999."
