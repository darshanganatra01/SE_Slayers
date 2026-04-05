from __future__ import annotations

from collections import OrderedDict
from decimal import Decimal

from flask_restx import Namespace, Resource

from app import db
from app.auth import AuthError, auth_required
from app.models.product import Product
from app.models.sku import SKU
from app.models.vendor import Vendor, VendorProduct

vendors_ns = Namespace("vendors", description="Vendor directory endpoints")


def _display_text(value: str | None) -> str:
    text = (value or "").strip()
    return text or "—"


def _serialize_vendor(vendor: Vendor) -> dict:
    return {
        "id": str(vendor.vid),
        "name": vendor.vendor_name,
        "prefix": (vendor.vendor_prefix or "").strip(),
        "leadTime": vendor.lead_time,
        "location": _display_text(vendor.location),
        "contact": {
            "phone": _display_text(vendor.contact),
            "email": _display_text(vendor.email),
        },
        "parts": [],
        "products": [],
        "partCount": 0,
        "_seen_products": set(),
    }


def _build_size_label(specs: dict | None) -> str:
    if not isinstance(specs, dict) or not specs:
        return "-"

    values = [str(value).strip() for value in specs.values() if str(value).strip()]
    if not values:
        return "-"
    return values[-1]


def _format_decimal(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _append_product(payload: dict, product: Product | None) -> None:
    if product is None or product.pid in payload["_seen_products"]:
        return

    payload["_seen_products"].add(product.pid)
    payload["parts"].append(product.pname)
    payload["products"].append(
        {
            "id": str(product.pid),
            "name": product.pname,
            "category": (product.category or "").strip(),
        }
    )
    payload["partCount"] = len(payload["products"])


def _finalize_vendor_payload(payload: dict) -> dict:
    payload.pop("_seen_products", None)
    return payload


def _sort_suppliers(suppliers: list[dict]) -> list[dict]:
    return sorted(
        suppliers,
        key=lambda supplier: (
            supplier["price"] is None,
            supplier["price"] if supplier["price"] is not None else float("inf"),
            supplier["vendor"]["name"].lower(),
        ),
    )


def _finalize_compare_part(payload: dict) -> dict:
    size_entries = []
    for size_payload in payload.pop("_sizes", OrderedDict()).values():
        size_payload["suppliers"] = _sort_suppliers(list(size_payload.pop("_suppliers", {}).values()))
        size_entries.append(size_payload)

    payload["sizes"] = size_entries
    return payload


@vendors_ns.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return {"message": error.message}, error.status_code


@vendors_ns.route("")
class VendorListResource(Resource):
    @auth_required("admin")
    def get(self):
        rows = (
            db.session.query(Vendor, Product)
            .outerjoin(VendorProduct, VendorProduct.vid == Vendor.vid)
            .outerjoin(Product, Product.pid == VendorProduct.pid)
            .order_by(Vendor.vendor_name.asc(), Product.pname.asc())
            .all()
        )

        grouped: OrderedDict[str, dict] = OrderedDict()

        for vendor, product in rows:
            payload = grouped.setdefault(vendor.vid, _serialize_vendor(vendor))
            _append_product(payload, product)

        vendors = [_finalize_vendor_payload(payload) for payload in grouped.values()]
        return {"vendors": vendors}, 200


@vendors_ns.route("/<string:vendor_id>")
class VendorDetailResource(Resource):
    @auth_required("admin")
    def get(self, vendor_id: str):
        vendor = Vendor.query.filter_by(vid=vendor_id).first()
        if vendor is None:
            vendors_ns.abort(404, "Vendor not found.")

        payload = _serialize_vendor(vendor)
        products = (
            Product.query.join(VendorProduct, VendorProduct.pid == Product.pid)
            .filter(VendorProduct.vid == vendor_id)
            .order_by(Product.pname.asc())
            .all()
        )
        for product in products:
            _append_product(payload, product)

        return {"vendor": _finalize_vendor_payload(payload)}, 200


@vendors_ns.route("/catalog/compare")
class VendorCompareCatalogResource(Resource):
    @auth_required("admin")
    def get(self):
        rows = (
            db.session.query(Product, SKU, Vendor)
            .outerjoin(VendorProduct, VendorProduct.pid == Product.pid)
            .outerjoin(SKU, SKU.vpid == VendorProduct.vpid)
            .outerjoin(Vendor, Vendor.vid == VendorProduct.vid)
            .order_by(Product.pid.asc(), Product.pname.asc(), SKU.skuid.asc())
            .all()
        )

        parts: OrderedDict[str, dict] = OrderedDict()

        for product, sku, vendor in rows:
            part_payload = parts.setdefault(
                product.pid,
                {
                    "id": str(product.pid),
                    "name": product.pname,
                    "image": None,
                    "sizes": [],
                    "_sizes": OrderedDict(),
                },
            )

            if sku is None or vendor is None:
                continue

            size_label = _build_size_label(sku.specs)
            size_payload = part_payload["_sizes"].setdefault(
                size_label,
                {
                    "size": size_label,
                    "suppliers": [],
                    "_suppliers": OrderedDict(),
                },
            )

            existing_supplier = size_payload["_suppliers"].get(vendor.vid)
            next_price = _format_decimal(sku.current_buy_rate)

            if (
                existing_supplier is None
                or existing_supplier["price"] is None
                or (next_price is not None and next_price < existing_supplier["price"])
            ):
                size_payload["_suppliers"][vendor.vid] = {
                    "vendorId": str(vendor.vid),
                    "price": next_price,
                    "leadTime": vendor.lead_time,
                    "vendor": {
                        "id": str(vendor.vid),
                        "name": vendor.vendor_name,
                        "location": _display_text(vendor.location),
                        "leadTime": vendor.lead_time,
                    },
                }

        return {"parts": [_finalize_compare_part(payload) for payload in parts.values()]}, 200
