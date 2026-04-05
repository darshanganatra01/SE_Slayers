from __future__ import annotations

import csv
import json
import random
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from app import db
from app.models.product import Product
from app.models.sku import SKU
from app.models.vendor import Vendor, VendorProduct

SEED_DIR = Path(__file__).resolve().parents[1] / "Seed_values"


def _load_csv(filename: str) -> list[dict[str, str]]:
    path = SEED_DIR / filename
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _to_int(value: str | None) -> int | None:
    cleaned = _clean(value)
    return int(cleaned) if cleaned is not None else None


def _to_decimal(value: str | None) -> Decimal | None:
    cleaned = _clean(value)
    return Decimal(cleaned) if cleaned is not None else None


def _compute_sell_price(buy_price: Decimal | None) -> Decimal | None:
    if buy_price is None:
        return None
    return (buy_price * Decimal("1.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def seed_products() -> int:
    rows = _load_csv("Product.csv")
    seeded = 0

    for row in rows:
        pid = row["PID"].strip()
        product = Product.query.filter_by(pid=pid).first()
        if product is None:
            product = Product(pid=pid)
            db.session.add(product)
            seeded += 1

        product.pname = row["PName"].strip()
        product.category = _clean(row.get("Category"))

    db.session.commit()
    return seeded


def seed_vendors() -> int:
    rows = _load_csv("Vendor.csv")
    seeded = 0

    for row in rows:
        vid = row["VID"].strip()
        vendor = Vendor.query.filter_by(vid=vid).first()
        if vendor is None:
            vendor = Vendor(vid=vid)
            db.session.add(vendor)
            seeded += 1

        vendor.vendor_name = row["VendorName"].strip()
        vendor.vendor_prefix = _clean(row.get("VendorPrefix"))
        vendor.lead_time = random.randint(3, 10)
        vendor.location = _clean(row.get("Location"))
        vendor.contact = _clean(row.get("Contact"))
        vendor.email = _clean(row.get("Email"))

    db.session.commit()
    return seeded


def seed_vendor_products() -> int:
    rows = _load_csv("VendorProduct.csv")
    seeded = 0

    for row in rows:
        vpid = row["VPID"].strip()
        vendor_product = VendorProduct.query.filter_by(vpid=vpid).first()
        if vendor_product is None:
            vendor_product = VendorProduct(vpid=vpid)
            db.session.add(vendor_product)
            seeded += 1

        vendor_product.vid = row["VID"].strip()
        vendor_product.pid = row["PID"].strip()

    db.session.commit()
    return seeded


def seed_skus() -> int:
    rows = _load_csv("SKU_table_2.csv")
    seeded = 0

    for row in rows:
        skuid = row["SKU ID"].strip()
        sku = SKU.query.filter_by(skuid=skuid).first()
        if sku is None:
            sku = SKU(skuid=skuid)
            db.session.add(sku)
            seeded += 1

        buy_rate = _to_decimal(row.get("Current_Buy"))

        sku.vpid = row["VendorProduct_ID"].strip()
        sku.unit_measurement_buy = _to_int(row.get("UnitMeasurementBuy"))
        sku.lot_size_buy = _to_int(row.get("LotSizeBuy"))
        sku.current_buy_rate = buy_rate
        sku.unit_measurement_sell = _to_int(row.get("UnitMeasurementSell"))
        sku.lot_size_sell = _to_int(row.get("LotSizeSell"))
        sku.current_sell_rate = _compute_sell_price(buy_rate)
        sku.specs = json.loads(row["Specs_JSON"])
        sku.stock_qty = random.randint(150, 500)
        sku.threshold = _to_int(row.get("Threshold"))

    db.session.commit()
    return seeded


def seed_catalog_from_csv() -> dict[str, int]:
    """Seed products, vendors, vendor-products, and skus from CSV files."""

    db.create_all()

    result = {
        "products": seed_products(),
        "vendors": seed_vendors(),
        "vendor_products": seed_vendor_products(),
        "skus": seed_skus(),
    }
    return result
