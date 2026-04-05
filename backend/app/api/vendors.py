from __future__ import annotations

from collections import OrderedDict
from datetime import date
from decimal import Decimal
from uuid import uuid4

from flask import request
from flask_restx import Namespace, Resource

from app import db
from app.auth import AuthError, auth_required, get_current_user
from app.models.product import Product
from app.models.sku import SKU
from app.models.vendor import Vendor, VendorProduct
from app.models.vendor_order import VendorOrder, VendorOrderDetail

vendors_ns = Namespace("vendors", description="Vendor directory endpoints")


def _display_text(value: str | None) -> str:
    text = (value or "").strip()
    return text or "—"


def _spec_values(specs: dict | None) -> list[str]:
    if not isinstance(specs, dict) or not specs:
        return []

    return [str(value).strip() for value in specs.values() if str(value).strip()]


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
    values = _spec_values(specs)
    if not values:
        return "-"

    return values[-1]


def _build_spec_label(specs: dict | None) -> str:
    values = _spec_values(specs)
    if len(values) <= 1:
        return ""
    return " · ".join(values[:-1])


def _build_spec_key(specs: dict | None) -> str:
    size = _build_size_label(specs)
    spec = _build_spec_label(specs)
    if spec:
        return f"{size}\n{spec}"
    return size


def _format_decimal(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _generate_vendor_order_id() -> str:
    return f"VO-{uuid4().hex[:8].upper()}"


def _generate_vendor_order_detail_id() -> str:
    return f"VOD-{uuid4().hex[:8].upper()}"


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


def _specification_display(specs: dict | None) -> str:
    size = _build_size_label(specs)
    spec = _build_spec_label(specs)
    if spec:
        return f"{size} · {spec}"
    return size


def _status_label(raw_status: str | None) -> str:
    normalized = (raw_status or "").strip().lower()
    if normalized == "completed":
        return "received"
    return "pending"


def _serialize_procurement(
    order: VendorOrder,
    detail: VendorOrderDetail | None,
    sku: SKU | None,
    vendor: Vendor | None,
    product: Product | None,
) -> dict:
    unit_measurement_buy = sku.unit_measurement_buy if sku is not None else None
    lot_size = sku.lot_size_buy if sku is not None else None
    ordered_qty = detail.ordered_qty if detail is not None else None
    lot_count = None
    if (
        ordered_qty is not None
        and unit_measurement_buy
        and lot_size
        and unit_measurement_buy > 0
        and lot_size > 0
    ):
        divisor = unit_measurement_buy * lot_size
        if ordered_qty % divisor == 0:
            lot_count = ordered_qty // divisor

    total_amount = order.total_amount if order.total_amount is not None else detail.amount if detail is not None else None

    return {
        "id": str(order.void),
        "vendorId": str(order.vid),
        "skuId": str(sku.skuid) if sku is not None else "",
        "partName": product.pname if product is not None else "Unknown Part",
        "specification": _specification_display(sku.specs if sku is not None else None),
        "orderDate": order.order_date.isoformat() if order.order_date else None,
        "status": _status_label(order.status),
        "statusRaw": (order.status or "").strip() or None,
        "currentBuy": _format_decimal(detail.agree_price if detail is not None else sku.current_buy_rate if sku is not None else None),
        "unitMeasurementBuy": unit_measurement_buy,
        "lotSize": lot_size,
        "lotCount": lot_count,
        "orderedQty": ordered_qty,
        "totalCost": _format_decimal(total_amount),
        "vendor": {
            "id": str(vendor.vid) if vendor is not None else str(order.vid),
            "name": vendor.vendor_name if vendor is not None else "Unknown Vendor",
            "location": _display_text(vendor.location if vendor is not None else None),
            "leadTime": vendor.lead_time if vendor is not None else None,
        },
    }


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
            spec_label = _build_spec_label(sku.specs)
            spec_key = _build_spec_key(sku.specs)
            size_payload = part_payload["_sizes"].setdefault(
                spec_key,
                {
                    "key": spec_key,
                    "size": size_label,
                    "spec": spec_label,
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
                    "skuId": str(sku.skuid),
                    "price": next_price,
                    "currentBuy": next_price,
                    "unitMeasurementBuy": sku.unit_measurement_buy,
                    "lotSize": sku.lot_size_buy,
                    "leadTime": vendor.lead_time,
                    "vendor": {
                        "id": str(vendor.vid),
                        "name": vendor.vendor_name,
                        "location": _display_text(vendor.location),
                        "leadTime": vendor.lead_time,
                    },
                }

        return {"parts": [_finalize_compare_part(payload) for payload in parts.values()]}, 200


@vendors_ns.route("/procurements")
class VendorProcurementCollectionResource(Resource):
    @auth_required("admin")
    def get(self):
        rows = (
            db.session.query(VendorOrder, VendorOrderDetail, SKU, Vendor, Product)
            .join(Vendor, Vendor.vid == VendorOrder.vid)
            .outerjoin(VendorOrderDetail, VendorOrderDetail.void == VendorOrder.void)
            .outerjoin(SKU, SKU.skuid == VendorOrderDetail.skuid)
            .outerjoin(VendorProduct, VendorProduct.vpid == SKU.vpid)
            .outerjoin(Product, Product.pid == VendorProduct.pid)
            .order_by(VendorOrder.order_date.desc(), VendorOrder.void.desc(), VendorOrderDetail.vo_detail_id.asc())
            .all()
        )

        procurements: OrderedDict[str, dict] = OrderedDict()
        for order, detail, sku, vendor, product in rows:
            if order.void in procurements:
                continue
            procurements[order.void] = _serialize_procurement(order, detail, sku, vendor, product)

        return {"procurements": list(procurements.values())}, 200

    @auth_required("admin")
    def post(self):
        payload = request.get_json(silent=True) or {}
        sku_id = str(payload.get("skuId") or "").strip()
        vendor_id = str(payload.get("vendorId") or "").strip()

        try:
            lot_count = int(payload.get("lotCount"))
        except (TypeError, ValueError):
            vendors_ns.abort(400, "Lot count must be a whole number.")

        if not sku_id:
            vendors_ns.abort(400, "A SKU must be selected for procurement.")
        if not vendor_id:
            vendors_ns.abort(400, "A vendor must be selected for procurement.")
        if lot_count <= 0:
            vendors_ns.abort(400, "Lot count must be at least 1.")

        row = (
            db.session.query(SKU, VendorProduct, Product, Vendor)
            .join(VendorProduct, VendorProduct.vpid == SKU.vpid)
            .join(Product, Product.pid == VendorProduct.pid)
            .join(Vendor, Vendor.vid == VendorProduct.vid)
            .filter(SKU.skuid == sku_id, Vendor.vid == vendor_id)
            .first()
        )
        if row is None:
            vendors_ns.abort(404, "Selected vendor specification was not found.")

        sku, _vendor_product, product, vendor = row
        if (
            sku.current_buy_rate is None
            or sku.unit_measurement_buy is None
            or sku.lot_size_buy is None
            or sku.unit_measurement_buy <= 0
            or sku.lot_size_buy <= 0
        ):
            vendors_ns.abort(400, "This SKU is missing procurement pricing or lot configuration.")

        user = get_current_user()
        ordered_qty = lot_count * sku.lot_size_buy * sku.unit_measurement_buy
        total_amount = sku.current_buy_rate * ordered_qty

        order = VendorOrder(
            void=_generate_vendor_order_id(),
            vid=vendor.vid,
            created_by=user.uid,
            order_date=date.today(),
            status="Confirmed",
            total_amount=total_amount,
        )
        detail = VendorOrderDetail(
            vo_detail_id=_generate_vendor_order_detail_id(),
            void=order.void,
            skuid=sku.skuid,
            ordered_qty=ordered_qty,
            agree_price=sku.current_buy_rate,
            amount=total_amount,
        )

        db.session.add(order)
        db.session.add(detail)
        db.session.commit()

        return {"procurement": _serialize_procurement(order, detail, sku, vendor, product)}, 201


@vendors_ns.route("/procurements/<string:procurement_id>/receive")
class VendorProcurementReceiveResource(Resource):
    @auth_required("admin")
    def patch(self, procurement_id: str):
        order = VendorOrder.query.filter_by(void=procurement_id).first()
        if order is None:
            vendors_ns.abort(404, "Procurement request not found.")

        details = (
            db.session.query(VendorOrderDetail, SKU)
            .join(SKU, SKU.skuid == VendorOrderDetail.skuid)
            .filter(VendorOrderDetail.void == procurement_id)
            .order_by(VendorOrderDetail.vo_detail_id.asc())
            .all()
        )

        if (order.status or "").strip().lower() != "completed":
            for detail, sku in details:
                sku.stock_qty = (sku.stock_qty or 0) + (detail.ordered_qty or 0)
            order.status = "Completed"

        db.session.commit()

        row = (
            db.session.query(VendorOrder, VendorOrderDetail, SKU, Vendor, Product)
            .join(Vendor, Vendor.vid == VendorOrder.vid)
            .outerjoin(VendorOrderDetail, VendorOrderDetail.void == VendorOrder.void)
            .outerjoin(SKU, SKU.skuid == VendorOrderDetail.skuid)
            .outerjoin(VendorProduct, VendorProduct.vpid == SKU.vpid)
            .outerjoin(Product, Product.pid == VendorProduct.pid)
            .filter(VendorOrder.void == procurement_id)
            .order_by(VendorOrderDetail.vo_detail_id.asc())
            .first()
        )
        if row is None:
            vendors_ns.abort(404, "Procurement request not found.")

        order, detail, sku, vendor, product = row
        return {"procurement": _serialize_procurement(order, detail, sku, vendor, product)}, 200
