from __future__ import annotations

from collections import OrderedDict, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
import re
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


def _clean_text(value: object | None) -> str:
    return str(value or "").strip()


def _display_text(value: str | None) -> str:
    text = _clean_text(value)
    return text or "—"


def _is_valid_vendor_phone(value: str | None) -> bool:
    contact = _clean_text(value)
    if not contact:
        return True

    digits = re.sub(r"\D", "", contact)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return len(digits) == 10


def _normalize_specs(specs: dict | None) -> dict:
    if not isinstance(specs, dict):
        return {}

    normalized = OrderedDict()
    for key, value in specs.items():
        text = _clean_text(value)
        if text:
            normalized[str(key)] = text
    return dict(normalized)


def _spec_values(specs: dict | None) -> list[str]:
    return list(_normalize_specs(specs).values())


def _specs_signature(specs: dict | None) -> tuple[str, ...]:
    return tuple(_spec_values(specs))


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
        "priceEntries": [],
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


def _generate_vendor_id() -> str:
    max_numeric = 0
    for (value,) in db.session.query(Vendor.vid).all():
        match = re.search(r"(\d+)$", str(value))
        if match:
            max_numeric = max(max_numeric, int(match.group(1)))
    return str(max_numeric + 1)


def _generate_vendor_product_id() -> str:
    return f"VP-{uuid4().hex[:8].upper()}"


def _generate_sku_id() -> str:
    return f"SKU-{uuid4().hex[:8].upper()}"


def _generate_vendor_order_id() -> str:
    return f"VO-{uuid4().hex[:8].upper()}"


def _generate_vendor_order_detail_id() -> str:
    return f"VOD-{uuid4().hex[:8].upper()}"


def _generate_vendor_prefix(name: str) -> str:
    parts = [part[0] for part in re.split(r"\s+", _clean_text(name)) if part]
    return "".join(parts).upper()


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


def _serialize_price_entry(product: Product, sku: SKU) -> dict:
    normalized_specs = _normalize_specs(sku.specs)
    return {
        "productId": str(product.pid),
        "skuId": str(sku.skuid),
        "key": _build_spec_key(normalized_specs),
        "size": _build_size_label(normalized_specs),
        "spec": _build_spec_label(normalized_specs),
        "specification": _specification_display(normalized_specs),
        "specs": normalized_specs,
        "price": _format_decimal(sku.current_buy_rate),
    }


def _load_active_vendor_products(vendor_id: str) -> list[Product]:
    rows = (
        db.session.query(Product, SKU)
        .join(VendorProduct, VendorProduct.pid == Product.pid)
        .outerjoin(SKU, SKU.vpid == VendorProduct.vpid)
        .filter(VendorProduct.vid == vendor_id)
        .order_by(Product.pname.asc(), SKU.skuid.asc())
        .all()
    )

    grouped: OrderedDict[str, dict] = OrderedDict()
    for product, sku in rows:
        state = grouped.setdefault(
            product.pid,
            {"product": product, "has_skus": False, "has_priced_skus": False},
        )
        if sku is None:
            continue
        state["has_skus"] = True
        if sku.current_buy_rate is not None:
            state["has_priced_skus"] = True

    return [
        state["product"]
        for state in grouped.values()
        if state["has_priced_skus"] or not state["has_skus"]
    ]


def _load_vendor_price_entries(vendor_id: str) -> list[dict]:
    rows = (
        db.session.query(Product, SKU)
        .join(VendorProduct, VendorProduct.pid == Product.pid)
        .join(SKU, SKU.vpid == VendorProduct.vpid)
        .filter(VendorProduct.vid == vendor_id, SKU.current_buy_rate.isnot(None))
        .order_by(Product.pname.asc(), SKU.skuid.asc())
        .all()
    )
    return [_serialize_price_entry(product, sku) for product, sku in rows]


def _serialize_vendor_details(vendor: Vendor) -> dict:
    payload = _serialize_vendor(vendor)
    for product in _load_active_vendor_products(vendor.vid):
        _append_product(payload, product)
    payload["priceEntries"] = _load_vendor_price_entries(vendor.vid)
    return _finalize_vendor_payload(payload)


def _coerce_lead_time(value: object | None) -> int | None:
    text = _clean_text(value)
    if not text:
        return None
    try:
        lead_time = int(text)
    except ValueError as error:
        raise ValueError("Lead time must be a whole number.") from error
    if lead_time < 0:
        raise ValueError("Lead time cannot be negative.")
    return lead_time


def _coerce_price(value: object | None) -> Decimal | None:
    text = _clean_text(value)
    if not text:
        return None
    try:
        amount = Decimal(text)
    except InvalidOperation as error:
        raise ValueError("Each price must be a valid number.") from error
    if amount < 0:
        raise ValueError("Prices cannot be negative.")
    return amount.quantize(Decimal("0.01"))


def _parse_product_ids(value: object | None) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Selected products must be sent as a list.")

    seen = set()
    product_ids: list[str] = []
    for raw_product_id in value:
        product_id = _clean_text(raw_product_id)
        if not product_id or product_id in seen:
            continue
        seen.add(product_id)
        product_ids.append(product_id)
    return product_ids


def _parse_price_entries(value: object | None) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Vendor prices must be sent as a list.")

    entries = []
    for raw_entry in value:
        if not isinstance(raw_entry, dict):
            raise ValueError("Each vendor price row must be an object.")

        product_id = _clean_text(raw_entry.get("productId"))
        specs = _normalize_specs(raw_entry.get("specs"))
        if not product_id or not specs:
            continue

        entries.append(
            {
                "productId": product_id,
                "specs": specs,
                "signature": _specs_signature(specs),
                "price": _coerce_price(raw_entry.get("price")),
            }
        )

    return entries


def _build_product_spec_templates(product_ids: list[str]) -> dict[str, dict[tuple[str, ...], dict]]:
    if not product_ids:
        return {}

    rows = (
        db.session.query(VendorProduct.pid, SKU)
        .join(SKU, SKU.vpid == VendorProduct.vpid)
        .filter(VendorProduct.pid.in_(product_ids))
        .order_by(VendorProduct.pid.asc(), SKU.skuid.asc())
        .all()
    )

    templates: dict[str, dict[tuple[str, ...], dict]] = defaultdict(dict)
    for product_id, sku in rows:
        signature = _specs_signature(sku.specs)
        if not signature or signature in templates[product_id]:
            continue

        templates[product_id][signature] = {
            "specs": _normalize_specs(sku.specs),
            "unit_measurement_buy": sku.unit_measurement_buy,
            "lot_size_buy": sku.lot_size_buy,
            "unit_measurement_sell": sku.unit_measurement_sell,
            "lot_size_sell": sku.lot_size_sell,
            "current_sell_rate": sku.current_sell_rate,
            "threshold": sku.threshold,
        }

    return templates


def _apply_sku_template(sku: SKU, template: dict | None) -> None:
    source = template or {}
    sku.unit_measurement_buy = sku.unit_measurement_buy if sku.unit_measurement_buy is not None else source.get("unit_measurement_buy", 1)
    sku.lot_size_buy = sku.lot_size_buy if sku.lot_size_buy is not None else source.get("lot_size_buy", 1)
    sku.unit_measurement_sell = sku.unit_measurement_sell if sku.unit_measurement_sell is not None else source.get("unit_measurement_sell", 1)
    sku.lot_size_sell = sku.lot_size_sell if sku.lot_size_sell is not None else source.get("lot_size_sell", 1)
    if sku.current_sell_rate is None:
        sku.current_sell_rate = source.get("current_sell_rate")
    if sku.threshold is None:
        sku.threshold = source.get("threshold", 0)
    if sku.stock_qty is None:
        sku.stock_qty = 0


def _validate_products(product_ids: list[str]) -> dict[str, Product]:
    if not product_ids:
        return {}

    products = Product.query.filter(Product.pid.in_(product_ids)).order_by(Product.pname.asc()).all()
    products_by_id = {product.pid: product for product in products}
    missing_product_ids = [product_id for product_id in product_ids if product_id not in products_by_id]
    if missing_product_ids:
        vendors_ns.abort(400, f"Unknown product selection: {', '.join(missing_product_ids)}.")
    return products_by_id


def _save_vendor_catalog(vendor: Vendor, product_ids: list[str], price_entries: list[dict]) -> None:
    selected_product_ids = set(product_ids)
    products_by_id = _validate_products(product_ids)
    templates_by_product = _build_product_spec_templates(product_ids)

    price_entries_by_product: dict[str, dict[tuple[str, ...], dict]] = defaultdict(dict)
    for entry in price_entries:
        product_id = entry["productId"]
        if product_id not in products_by_id:
            vendors_ns.abort(400, f"Unknown product in price list: {product_id}.")
        price_entries_by_product[product_id][entry["signature"]] = entry

    existing_vendor_products = {
        vendor_product.pid: vendor_product
        for vendor_product in VendorProduct.query.filter_by(vid=vendor.vid).all()
    }

    for product_id in product_ids:
        vendor_product = existing_vendor_products.get(product_id)
        if vendor_product is None:
            vendor_product = VendorProduct(
                vpid=_generate_vendor_product_id(),
                vid=vendor.vid,
                pid=product_id,
            )
            db.session.add(vendor_product)
            db.session.flush()
            existing_vendor_products[product_id] = vendor_product

        existing_skus = {
            _specs_signature(sku.specs): sku
            for sku in vendor_product.skus.order_by(SKU.skuid.asc()).all()
            if _specs_signature(sku.specs)
        }
        selected_entries = price_entries_by_product.get(product_id, {})

        for signature, entry in selected_entries.items():
            sku = existing_skus.get(signature)
            if entry["price"] is None:
                if sku is not None:
                    sku.current_buy_rate = None
                continue

            if sku is None:
                sku = SKU(
                    skuid=_generate_sku_id(),
                    vpid=vendor_product.vpid,
                    specs=entry["specs"],
                    stock_qty=0,
                )
                db.session.add(sku)
                existing_skus[signature] = sku
            else:
                sku.specs = entry["specs"]

            _apply_sku_template(sku, templates_by_product.get(product_id, {}).get(signature))
            sku.current_buy_rate = entry["price"]

        for signature, sku in existing_skus.items():
            if signature not in selected_entries:
                sku.current_buy_rate = None

    for product_id, vendor_product in existing_vendor_products.items():
        if product_id in selected_product_ids:
            continue

        existing_skus = vendor_product.skus.order_by(SKU.skuid.asc()).all()
        if not existing_skus:
            db.session.delete(vendor_product)
            continue

        for sku in existing_skus:
            sku.current_buy_rate = None


def _parse_vendor_request(payload: dict) -> dict:
    name = _clean_text(payload.get("name"))
    if not name:
        vendors_ns.abort(400, "Vendor name is required.")

    contact = _clean_text(payload.get("phone") or payload.get("contact"))
    if not _is_valid_vendor_phone(contact):
        vendors_ns.abort(400, "Phone number must be 10 digits. +91 in front is okay.")

    try:
        lead_time = _coerce_lead_time(payload.get("leadTime"))
        product_ids = _parse_product_ids(payload.get("productIds"))
        price_entries = _parse_price_entries(payload.get("prices"))
    except ValueError as error:
        vendors_ns.abort(400, str(error))

    return {
        "name": name,
        "location": _clean_text(payload.get("address") or payload.get("location")),
        "contact": contact,
        "email": _clean_text(payload.get("email")),
        "lead_time": lead_time,
        "product_ids": product_ids,
        "price_entries": price_entries,
    }


@vendors_ns.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return {"message": error.message}, error.status_code


@vendors_ns.route("")
class VendorListResource(Resource):
    @auth_required("admin")
    def get(self):
        vendors = Vendor.query.order_by(Vendor.vendor_name.asc()).all()
        payload = [_serialize_vendor_details(vendor) for vendor in vendors]
        return {"vendors": payload}, 200

    @auth_required("admin")
    def post(self):
        payload = _parse_vendor_request(request.get_json(silent=True) or {})

        vendor = Vendor(
            vid=_generate_vendor_id(),
            vendor_name=payload["name"],
            vendor_prefix=_generate_vendor_prefix(payload["name"]),
            lead_time=payload["lead_time"],
            location=payload["location"] or None,
            contact=payload["contact"] or None,
            email=payload["email"] or None,
        )
        db.session.add(vendor)
        db.session.flush()

        _save_vendor_catalog(vendor, payload["product_ids"], payload["price_entries"])
        db.session.commit()

        return {"vendor": _serialize_vendor_details(vendor)}, 201


@vendors_ns.route("/<string:vendor_id>")
class VendorDetailResource(Resource):
    @auth_required("admin")
    def get(self, vendor_id: str):
        vendor = Vendor.query.filter_by(vid=vendor_id).first()
        if vendor is None:
            vendors_ns.abort(404, "Vendor not found.")

        return {"vendor": _serialize_vendor_details(vendor)}, 200

    @auth_required("admin")
    def patch(self, vendor_id: str):
        vendor = Vendor.query.filter_by(vid=vendor_id).first()
        if vendor is None:
            vendors_ns.abort(404, "Vendor not found.")

        payload = _parse_vendor_request(request.get_json(silent=True) or {})

        vendor.vendor_name = payload["name"]
        vendor.vendor_prefix = _generate_vendor_prefix(payload["name"])
        vendor.lead_time = payload["lead_time"]
        vendor.location = payload["location"] or None
        vendor.contact = payload["contact"] or None
        vendor.email = payload["email"] or None

        _save_vendor_catalog(vendor, payload["product_ids"], payload["price_entries"])
        db.session.commit()

        return {"vendor": _serialize_vendor_details(vendor)}, 200

    @auth_required("admin")
    def delete(self, vendor_id: str):
        vendor = Vendor.query.filter_by(vid=vendor_id).first()
        if vendor is None:
            vendors_ns.abort(404, "Vendor not found.")

        has_procurement_history = VendorOrder.query.filter_by(vid=vendor_id).first() is not None
        if has_procurement_history:
            vendors_ns.abort(400, "Vendor cannot be deleted because procurement history exists.")

        vendor_products = VendorProduct.query.filter_by(vid=vendor_id).all()
        for vendor_product in vendor_products:
            for sku in vendor_product.skus.order_by(SKU.skuid.asc()).all():
                db.session.delete(sku)
            db.session.delete(vendor_product)

        db.session.delete(vendor)
        db.session.commit()
        return "", 204


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

            if sku is None:
                continue

            normalized_specs = _normalize_specs(sku.specs)
            spec_key = _build_spec_key(normalized_specs)
            size_payload = part_payload["_sizes"].setdefault(
                spec_key,
                {
                    "key": spec_key,
                    "size": _build_size_label(normalized_specs),
                    "spec": _build_spec_label(normalized_specs),
                    "specs": normalized_specs,
                    "suppliers": [],
                    "_suppliers": OrderedDict(),
                },
            )

            if vendor is None or sku.current_buy_rate is None:
                continue

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
