from __future__ import annotations

from collections import OrderedDict
from datetime import date
from decimal import Decimal
from decimal import InvalidOperation
import json
import re
from uuid import uuid4

from app import db
from app.catalog_utils import ensure_product_image_dir, product_image_url
from flask import request, send_from_directory
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from app.auth import AuthError, auth_required
from app.models.product import Product
from app.models.sku import SKU
from app.models.vendor import Vendor, VendorProduct

inventory_ns = Namespace("inventory", description="Inventory endpoints")
PRODUCT_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "avif"}


def _stock_status(stock_qty: int | None, threshold: int | None) -> str:
    stock = stock_qty or 0
    limit = threshold or 0

    if stock == 0:
        return "out"
    if stock >= limit:
        return "instock"
    return "low"


def _format_decimal(value: Decimal | None) -> float:
    return float(value) if value is not None else 0.0


def _clean_text(value: object | None) -> str:
    return str(value or "").strip()


def _hidden_procurement_sku(stock_qty: int | None, threshold: int | None, sell_rate: Decimal | None) -> bool:
    return (stock_qty or 0) == 0 and (threshold or 0) == 0 and sell_rate is None


def _spec_values(specs: dict | None) -> list[str]:
    if not isinstance(specs, dict) or not specs:
        return []

    return [str(value).strip() for value in specs.values() if str(value).strip()]


def _normalize_specs(specs: dict | None) -> dict[str, str]:
    if not isinstance(specs, dict):
        return {}

    normalized: dict[str, str] = {}
    for key, value in specs.items():
        text = str(value or "").strip()
        if text:
            normalized[str(key)] = text
    return normalized


def _spec_signature(specs: dict | None) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(_normalize_specs(specs).items()))


def _spec_label(specs: dict | None) -> str:
    values = _spec_values(specs)
    return values[0] if values else ""


def _build_spec_display(specs: dict | None) -> tuple[str, str]:
    values = _spec_values(specs)
    if not values:
        return "-", ""

    size = values[-1]
    detail_values = values[:-1]
    details = " · ".join(detail_values)
    return size, details


def _build_spec_key(specs: dict | None) -> str:
    size, details = _build_spec_display(specs)
    if details:
        return f"{size}\n{details}"
    return size


def _portfolio_chip_status(status: str) -> str:
    if status == "instock":
        return "ok"
    return status


def _status_rank(status: str) -> int:
    ranks = {"instock": 3, "low": 2, "out": 1}
    return ranks.get(status, 0)


def _sku_priority(sku: SKU) -> tuple[int, int, int, int]:
    return (
        1 if sku.current_sell_rate is not None else 0,
        1 if (sku.threshold or 0) > 0 else 0,
        sku.stock_qty or 0,
        1 if sku.current_buy_rate is not None else 0,
    )


def _sku_has_history(sku: SKU) -> bool:
    return any(
        (
            sku.vendor_order_details.count() > 0,
            sku.vendor_invoice_details.count() > 0,
            sku.vendor_return_details.count() > 0,
            sku.customer_inv_details.count() > 0,
            sku.customer_order_details.count() > 0,
            sku.customer_return_details.count() > 0,
            sku.packing_slip_details.count() > 0,
            sku.stock_adjustments.count() > 0,
            len(sku.delivery_receipt_details) > 0,
        )
    )


def _generate_product_id() -> str:
    max_numeric = 0
    for (value,) in db.session.query(Product.pid).all():
        match = re.search(r"(\d+)$", str(value))
        if match:
            max_numeric = max(max_numeric, int(match.group(1)))
    return str(max_numeric + 1)


def _generate_vendor_product_id() -> str:
    return f"VP-{uuid4().hex[:8].upper()}"


def _generate_sku_id() -> str:
    return f"SKU-{uuid4().hex[:8].upper()}"


def _coerce_int(value: object | None, field_name: str, *, minimum: int | None = None) -> int:
    text = _clean_text(value)
    if text == "":
        raise ValueError(f"{field_name} is required.")
    try:
        parsed = int(text)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a whole number.") from error
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    return parsed


def _coerce_decimal(value: object | None, field_name: str, *, minimum: Decimal | None = None) -> Decimal:
    text = _clean_text(value)
    if text == "":
        raise ValueError(f"{field_name} is required.")
    try:
        parsed = Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"{field_name} must be a valid number.") from error
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    return parsed.quantize(Decimal("0.01"))


def _parse_create_part_payload(raw_payload: dict | None, allow_empty_vendor_prices: bool = False) -> dict:
    payload = raw_payload or {}
    name = _clean_text(payload.get("name"))
    category = _clean_text(payload.get("category"))
    if not name:
        raise ValueError("Product name is required.")
    if not category:
        raise ValueError("Category is required.")

    raw_vendor_ids = payload.get("vendorIds")
    if not isinstance(raw_vendor_ids, list):
        raise ValueError("Selected vendors must be sent as a list.")

    vendor_ids: list[str] = []
    seen_vendor_ids: set[str] = set()
    for raw_vendor_id in raw_vendor_ids:
        vendor_id = _clean_text(raw_vendor_id)
        if not vendor_id or vendor_id in seen_vendor_ids:
            continue
        vendor_ids.append(vendor_id)
        seen_vendor_ids.add(vendor_id)

    if not vendor_ids:
        raise ValueError("Select at least one vendor so the new specifications can be stored.")

    raw_specs = payload.get("specs")
    if not isinstance(raw_specs, list) or not raw_specs:
        raise ValueError("Add at least one specification.")

    specs: list[dict] = []
    seen_labels: set[str] = set()
    vendor_set = set(vendor_ids)
    for index, raw_spec in enumerate(raw_specs, start=1):
        if not isinstance(raw_spec, dict):
            raise ValueError("Each specification row must be an object.")

        label = _clean_text(raw_spec.get("label"))
        normalized_label = label.casefold()
        if not label:
            raise ValueError(f"Specification {index} is required.")
        if normalized_label in seen_labels:
            raise ValueError(f"Duplicate specification found: {label}.")

        raw_vendor_prices = raw_spec.get("vendorPrices")
        if not isinstance(raw_vendor_prices, list):
            raise ValueError(f"Specification {label} must include vendor prices.")

        vendor_prices: dict[str, Decimal | None] = {}
        for raw_price in raw_vendor_prices:
            if not isinstance(raw_price, dict):
                raise ValueError(f"Each vendor price row for {label} must be an object.")
            vendor_id = _clean_text(raw_price.get("vendorId"))
            if vendor_id not in vendor_set:
                continue
            raw_unit_buy_price = raw_price.get("unitBuyPrice")
            if allow_empty_vendor_prices and _clean_text(raw_unit_buy_price) == "":
                vendor_prices[vendor_id] = None
                continue
            vendor_prices[vendor_id] = _coerce_decimal(
                raw_unit_buy_price,
                f"Unit buy price for {label} / vendor {vendor_id}",
                minimum=Decimal("0"),
            )

        missing_vendor_prices = [vendor_id for vendor_id in vendor_ids if vendor_id not in vendor_prices]
        if missing_vendor_prices and not allow_empty_vendor_prices:
            raise ValueError(
                f"Enter unit buy prices for every selected vendor for {label}."
            )
        if not vendor_prices:
            raise ValueError(f"Enter at least one unit buy price for {label}.")

        specs.append(
            {
                "label": label,
                "specs": {"spec1": label},
                "stock_qty": _coerce_int(raw_spec.get("stockQty"), f"Current stock for {label}", minimum=0),
                "threshold": _coerce_int(raw_spec.get("threshold"), f"Threshold for {label}", minimum=0),
                "sell_price": _coerce_decimal(raw_spec.get("sellPrice"), f"Sell price for {label}", minimum=Decimal("0")),
                "vendor_prices": vendor_prices,
            }
        )
        seen_labels.add(normalized_label)

    unit_measurement_buy = _coerce_int(payload.get("unitMeasurementBuy"), "Unit measurement buy", minimum=1)
    lot_size_buy = _coerce_int(payload.get("lotSizeBuy"), "Lot size buy", minimum=1)

    return {
        "name": name,
        "category": category,
        "vendor_ids": vendor_ids,
        "unit_measurement_buy": unit_measurement_buy,
        "lot_size_buy": lot_size_buy,
        "specs": specs,
    }


def _parse_create_part_request(allow_empty_vendor_prices: bool = False) -> tuple[dict, object | None]:
    if request.content_type and "multipart/form-data" in request.content_type.lower():
        payload_text = request.form.get("payload", "").strip()
        if not payload_text:
            raise ValueError("Part details are required.")
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as error:
            raise ValueError("Part details could not be read.") from error
        return _parse_create_part_payload(payload, allow_empty_vendor_prices=allow_empty_vendor_prices), request.files.get("image")

    return _parse_create_part_payload(
        request.get_json(silent=True) or {},
        allow_empty_vendor_prices=allow_empty_vendor_prices,
    ), None


def _save_product_image(image_file, product_id: str) -> str | None:
    if image_file is None:
        return None

    original_name = secure_filename(image_file.filename or "")
    if not original_name:
        return None

    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in PRODUCT_IMAGE_EXTENSIONS:
        raise ValueError("Product image must be a PNG, JPG, JPEG, WEBP, or AVIF file.")

    image_dir = ensure_product_image_dir()
    filename = f"{product_id}-{uuid4().hex[:12]}.{extension}"
    image_file.save(image_dir / filename)
    return filename


def _create_part(payload: dict, image_file) -> Product:
    vendors = Vendor.query.filter(Vendor.vid.in_(payload["vendor_ids"])).all()
    vendors_by_id = {vendor.vid: vendor for vendor in vendors}
    missing_vendor_ids = [vendor_id for vendor_id in payload["vendor_ids"] if vendor_id not in vendors_by_id]
    if missing_vendor_ids:
        raise ValueError(f"Unknown vendor selection: {', '.join(missing_vendor_ids)}.")

    product = Product(
        pid=_generate_product_id(),
        pname=payload["name"],
        category=payload["category"],
    )
    db.session.add(product)
    db.session.flush()

    image_filename = None
    try:
        image_filename = _save_product_image(image_file, product.pid)
        product.image_filename = image_filename

        vendor_products: dict[str, VendorProduct] = {}
        for vendor_id in payload["vendor_ids"]:
            vendor_product = VendorProduct(
                vpid=_generate_vendor_product_id(),
                vid=vendor_id,
                pid=product.pid,
            )
            db.session.add(vendor_product)
            db.session.flush()
            vendor_products[vendor_id] = vendor_product

        opening_stock_vendor_id = payload["vendor_ids"][0]
        for spec in payload["specs"]:
            for vendor_id in payload["vendor_ids"]:
                applies_opening_stock = vendor_id == opening_stock_vendor_id
                db.session.add(
                    SKU(
                        skuid=_generate_sku_id(),
                        vpid=vendor_products[vendor_id].vpid,
                        unit_measurement_buy=payload["unit_measurement_buy"],
                        lot_size_buy=payload["lot_size_buy"],
                        current_buy_rate=spec["vendor_prices"][vendor_id],
                        unit_measurement_sell=1,
                        lot_size_sell=1,
                        current_sell_rate=spec["sell_price"] if applies_opening_stock else None,
                        specs=spec["specs"],
                        stock_qty=spec["stock_qty"] if applies_opening_stock else 0,
                        threshold=spec["threshold"] if applies_opening_stock else 0,
                    )
                )

        db.session.commit()
        return product
    except Exception:
        db.session.rollback()
        if image_filename:
            image_path = ensure_product_image_dir() / image_filename
            if image_path.exists():
                image_path.unlink()
        raise


def _serialize_part_for_form(product: Product) -> dict:
    rows = (
        db.session.query(VendorProduct.vid, SKU)
        .join(SKU, SKU.vpid == VendorProduct.vpid)
        .filter(VendorProduct.pid == product.pid)
        .order_by(VendorProduct.vid.asc(), SKU.skuid.asc())
        .all()
    )

    vendor_ids: list[str] = []
    specs_by_signature: OrderedDict[tuple[tuple[str, str], ...], dict] = OrderedDict()

    for vendor_id, sku in rows:
        vendor_id = str(vendor_id)
        if vendor_id not in vendor_ids:
            vendor_ids.append(vendor_id)

        signature = _spec_signature(sku.specs)
        if not signature:
            continue

        spec_payload = specs_by_signature.setdefault(
            signature,
            {
                "label": _spec_label(sku.specs),
                "vendor_prices": {},
                "_source_sku": sku,
                "_source_vendor_id": vendor_id,
            },
        )
        spec_payload["vendor_prices"][vendor_id] = (
            float(sku.current_buy_rate) if sku.current_buy_rate is not None else None
        )

        current_source = spec_payload["_source_sku"]
        if current_source is None or _sku_priority(sku) > _sku_priority(current_source):
            spec_payload["_source_sku"] = sku
            spec_payload["_source_vendor_id"] = vendor_id

    source_vendor_id = None
    for spec_payload in specs_by_signature.values():
        candidate_vendor_id = spec_payload.get("_source_vendor_id")
        if candidate_vendor_id in vendor_ids:
            source_vendor_id = candidate_vendor_id
            break

    if source_vendor_id is not None:
        vendor_ids = [source_vendor_id, *[vendor_id for vendor_id in vendor_ids if vendor_id != source_vendor_id]]

    specs: list[dict] = []
    for spec_payload in specs_by_signature.values():
        source_sku = spec_payload.get("_source_sku")
        specs.append(
            {
                "label": spec_payload["label"],
                "stockQty": source_sku.stock_qty if source_sku is not None and source_sku.stock_qty is not None else 0,
                "threshold": source_sku.threshold if source_sku is not None and source_sku.threshold is not None else 0,
                "sellPrice": float(source_sku.current_sell_rate) if source_sku is not None and source_sku.current_sell_rate is not None else 0.0,
                "vendorPrices": [
                    {
                        "vendorId": vendor_id,
                        "unitBuyPrice": spec_payload["vendor_prices"].get(vendor_id),
                    }
                    for vendor_id in vendor_ids
                ],
                "isExisting": True,
            }
        )

    source_sku = next(
        (
            spec_payload.get("_source_sku")
            for spec_payload in specs_by_signature.values()
            if spec_payload.get("_source_sku") is not None
        ),
        None,
    )

    return {
        "id": str(product.pid),
        "name": product.pname,
        "category": product.category or "",
        "image": product_image_url(product.image_filename),
        "unitMeasurementBuy": source_sku.unit_measurement_buy if source_sku is not None and source_sku.unit_measurement_buy is not None else 1,
        "lotSizeBuy": source_sku.lot_size_buy if source_sku is not None and source_sku.lot_size_buy is not None else 1,
        "vendorIds": vendor_ids,
        "specs": specs,
    }


def _update_part(product: Product, payload: dict, image_file) -> Product:
    vendors = Vendor.query.filter(Vendor.vid.in_(payload["vendor_ids"])).all()
    vendors_by_id = {vendor.vid: vendor for vendor in vendors}
    missing_vendor_ids = [vendor_id for vendor_id in payload["vendor_ids"] if vendor_id not in vendors_by_id]
    if missing_vendor_ids:
        raise ValueError(f"Unknown vendor selection: {', '.join(missing_vendor_ids)}.")

    existing_vendor_products = {
        vendor_product.vid: vendor_product
        for vendor_product in VendorProduct.query.filter_by(pid=product.pid).all()
    }
    existing_skus: dict[tuple[str, str], SKU] = {}
    existing_source_vendor_by_label: dict[str, str] = {}

    for vendor_id, vendor_product in existing_vendor_products.items():
        for sku in vendor_product.skus.order_by(SKU.skuid.asc()).all():
            label = _spec_label(sku.specs).casefold()
            if not label:
                continue
            existing_skus[(vendor_id, label)] = sku

            current_source = existing_source_vendor_by_label.get(label)
            if current_source is None:
                existing_source_vendor_by_label[label] = vendor_id
                continue

            current_source_sku = existing_skus.get((current_source, label))
            if current_source_sku is None or _sku_priority(sku) > _sku_priority(current_source_sku):
                existing_source_vendor_by_label[label] = vendor_id

    old_image_filename = product.image_filename
    new_image_filename = None
    desired_pairs: set[tuple[str, str]] = set()

    try:
        product.pname = payload["name"]
        product.category = payload["category"]

        should_replace_image = image_file is not None and bool(secure_filename(image_file.filename or ""))
        if should_replace_image:
            new_image_filename = _save_product_image(image_file, product.pid)
            product.image_filename = new_image_filename

        vendor_products = dict(existing_vendor_products)
        for vendor_id in payload["vendor_ids"]:
            if vendor_id in vendor_products:
                continue
            vendor_product = VendorProduct(
                vpid=_generate_vendor_product_id(),
                vid=vendor_id,
                pid=product.pid,
            )
            db.session.add(vendor_product)
            db.session.flush()
            vendor_products[vendor_id] = vendor_product

        for spec in payload["specs"]:
            label_key = spec["label"].casefold()
            priced_vendor_ids = [
                vendor_id for vendor_id in payload["vendor_ids"]
                if vendor_id in spec["vendor_prices"]
            ]
            source_vendor_id = existing_source_vendor_by_label.get(label_key)
            if source_vendor_id not in priced_vendor_ids:
                source_vendor_id = priced_vendor_ids[0]

            for vendor_id in priced_vendor_ids:
                desired_pairs.add((vendor_id, label_key))
                sku = existing_skus.get((vendor_id, label_key))
                if sku is None:
                    sku = SKU(
                        skuid=_generate_sku_id(),
                        vpid=vendor_products[vendor_id].vpid,
                    )
                    db.session.add(sku)
                    existing_skus[(vendor_id, label_key)] = sku

                sku.specs = spec["specs"]
                sku.unit_measurement_buy = payload["unit_measurement_buy"]
                sku.lot_size_buy = payload["lot_size_buy"]
                sku.unit_measurement_sell = sku.unit_measurement_sell if sku.unit_measurement_sell is not None else 1
                sku.lot_size_sell = sku.lot_size_sell if sku.lot_size_sell is not None else 1
                sku.current_buy_rate = spec["vendor_prices"][vendor_id]

                if vendor_id == source_vendor_id:
                    sku.current_sell_rate = spec["sell_price"]
                    sku.stock_qty = spec["stock_qty"]
                    sku.threshold = spec["threshold"]
                else:
                    sku.current_sell_rate = None
                    sku.stock_qty = 0
                    sku.threshold = 0

        for (vendor_id, label_key), sku in list(existing_skus.items()):
            if (vendor_id, label_key) in desired_pairs:
                continue
            if _sku_has_history(sku):
                raise ValueError(
                    f"Cannot remove specification '{_spec_label(sku.specs)}' from vendor {vendor_id} because transaction history exists."
                )
            db.session.delete(sku)

        db.session.flush()

        for vendor_product in vendor_products.values():
            remaining_skus = vendor_product.skus.order_by(SKU.skuid.asc()).all()
            if remaining_skus:
                continue
            db.session.delete(vendor_product)

        db.session.commit()

        if new_image_filename and old_image_filename and old_image_filename != new_image_filename:
            old_image_path = ensure_product_image_dir() / old_image_filename
            if old_image_path.exists():
                old_image_path.unlink()

        return product
    except Exception:
        db.session.rollback()
        if new_image_filename:
            image_path = ensure_product_image_dir() / new_image_filename
            if image_path.exists():
                image_path.unlink()
        raise


def _build_portfolio_products() -> tuple[list[dict], dict[str, dict]]:
    rows = (
        db.session.query(
            Product.pid,
            Product.pname,
            Product.category,
            Product.image_filename,
            SKU.skuid,
            SKU.specs,
            SKU.stock_qty,
            SKU.threshold,
            SKU.current_sell_rate,
        )
        .outerjoin(VendorProduct, VendorProduct.pid == Product.pid)
        .outerjoin(SKU, SKU.vpid == VendorProduct.vpid)
        .order_by(Product.pid.asc(), Product.pname.asc(), SKU.skuid.asc())
        .all()
    )

    grouped_products: OrderedDict[str, dict] = OrderedDict()
    detail_map: dict[str, dict] = {}

    for row in rows:
        product_key = str(row.pid)
        if product_key not in grouped_products:
            grouped_products[product_key] = {
                "name": row.pname,
                "category": row.category or "",
                "key": product_key,
                "image": product_image_url(row.image_filename),
                "sizes": [],
            }
            detail_map[product_key] = {
                "title": row.pname,
                "category": row.category or "",
                "rows": [],
                "_size_index": {},
            }

        if row.skuid is None:
            continue
        if _hidden_procurement_sku(row.stock_qty, row.threshold, row.current_sell_rate):
            continue

        status = _stock_status(row.stock_qty, row.threshold)
        size, spec = _build_spec_display(row.specs)
        spec_key = _build_spec_key(row.specs)
        chip_status = _portfolio_chip_status(status)

        chip_index = next(
            (index for index, item in enumerate(grouped_products[product_key]["sizes"]) if item["key"] == spec_key),
            None,
        )
        if chip_index is None:
            grouped_products[product_key]["sizes"].append(
                {
                    "key": spec_key,
                    "label": size,
                    "detail": spec,
                    "status": chip_status,
                }
            )
        else:
            existing = grouped_products[product_key]["sizes"][chip_index]["status"]
            if _status_rank(status) > _status_rank("instock" if existing == "ok" else existing):
                grouped_products[product_key]["sizes"][chip_index]["status"] = chip_status

        popup_data = detail_map[product_key]
        size_index = popup_data["_size_index"]
        if spec_key not in size_index:
            popup_data["rows"].append(
                {
                    "key": spec_key,
                    "size": size,
                    "dim": spec,
                    "stock": row.stock_qty or 0,
                    "maxStock": row.threshold or 0,
                    "status": chip_status,
                }
            )
            size_index[spec_key] = len(popup_data["rows"]) - 1
        else:
            detail_row = popup_data["rows"][size_index[spec_key]]
            detail_row["stock"] += row.stock_qty or 0
            detail_row["maxStock"] += row.threshold or 0
            if _status_rank(status) > _status_rank("instock" if detail_row["status"] == "ok" else detail_row["status"]):
                detail_row["status"] = chip_status
            if spec and not detail_row["dim"]:
                detail_row["dim"] = spec

    portfolio_products = list(grouped_products.values())
    for payload in detail_map.values():
        payload.pop("_size_index", None)

    return portfolio_products, detail_map


@inventory_ns.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return {"message": error.message}, error.status_code


@inventory_ns.route("/product-images/<string:filename>")
class InventoryProductImageResource(Resource):
    def get(self, filename: str):
        return send_from_directory(ensure_product_image_dir(), filename)


@inventory_ns.route("/overview")
class InventoryOverviewResource(Resource):
    @auth_required("admin")
    def get(self):
        rows = (
            SKU.query.join(VendorProduct, SKU.vpid == VendorProduct.vpid)
            .join(Product, VendorProduct.pid == Product.pid)
            .with_entities(
                SKU.skuid,
                SKU.vpid,
                SKU.specs,
                SKU.stock_qty,
                SKU.threshold,
                SKU.current_sell_rate,
                Product.pid,
                Product.pname,
                Product.category,
                Product.image_filename,
            )
            .order_by(Product.pname.asc(), SKU.skuid.asc())
            .all()
        )

        parts = []
        total_inventory_value = Decimal("0.00")

        for row in rows:
            if _hidden_procurement_sku(row.stock_qty, row.threshold, row.current_sell_rate):
                continue
            stock = row.stock_qty or 0
            threshold = row.threshold or 0
            status = _stock_status(stock, threshold)
            size, spec = _build_spec_display(row.specs)
            sell_price = row.current_sell_rate or Decimal("0.00")

            total_inventory_value += sell_price * stock

            parts.append(
                {
                    "id": row.skuid,
                    "skuId": row.skuid,
                    "sku": row.skuid,
                    "vpid": row.vpid,
                    "pid": row.pid,
                    "name": row.pname,
                    "category": row.category,
                    "image": product_image_url(row.image_filename),
                    "size": size,
                    "dims": "",
                    "spec": spec,
                    "stock": stock,
                    "threshold": threshold,
                    "maxStock": threshold if threshold > 0 else max(stock, 1),
                    "status": status,
                    "sellPrice": _format_decimal(sell_price),
                }
            )

        summary = {
            "totalParts": len(parts),
            "inStockCount": sum(1 for part in parts if part["status"] == "instock"),
            "lowStockCount": sum(1 for part in parts if part["status"] == "low" or part["status"] == "out"),
            "lowOnlyCount": sum(1 for part in parts if part["status"] == "low"),
            "outOfStockCount": sum(1 for part in parts if part["status"] == "out"),
            "inventoryValue": _format_decimal(total_inventory_value),
            "asOfDate": date.today().isoformat(),
        }

        portfolio_products, portfolio_details = _build_portfolio_products()

        return {
            "summary": summary,
            "parts": parts,
            "portfolioProducts": portfolio_products,
            "portfolioDetails": portfolio_details,
        }, 200


@inventory_ns.route("/parts")
class InventoryPartCollectionResource(Resource):
    @auth_required("admin")
    def get(self):
        product_id = _clean_text(request.args.get("productId"))
        if not product_id:
            inventory_ns.abort(400, "productId is required.")

        product = Product.query.filter_by(pid=product_id).first()
        if product is None:
            inventory_ns.abort(404, "Part not found.")

        return {"product": _serialize_part_for_form(product)}, 200

    @auth_required("admin")
    def post(self):
        try:
            payload, image_file = _parse_create_part_request()
            product = _create_part(payload, image_file)
        except ValueError as error:
            inventory_ns.abort(400, str(error))

        return {
            "product": {
                "id": str(product.pid),
                "name": product.pname,
                "category": product.category or "",
                "image": product_image_url(product.image_filename),
                "vendorIds": payload["vendor_ids"],
                "specCount": len(payload["specs"]),
            }
        }, 201

    @auth_required("admin")
    def patch(self):
        product_id = _clean_text(request.args.get("productId"))
        if not product_id:
            inventory_ns.abort(400, "productId is required.")

        product = Product.query.filter_by(pid=product_id).first()
        if product is None:
            inventory_ns.abort(404, "Part not found.")

        try:
            payload, image_file = _parse_create_part_request(allow_empty_vendor_prices=True)
            product = _update_part(product, payload, image_file)
        except ValueError as error:
            inventory_ns.abort(400, str(error))

        return {"product": _serialize_part_for_form(product)}, 200


@inventory_ns.route("/parts/<path:product_id>")
class InventoryPartDetailResource(Resource):
    @auth_required("admin")
    def get(self, product_id: str):
        product = Product.query.filter_by(pid=product_id).first()
        if product is None:
            inventory_ns.abort(404, "Part not found.")

        return {"product": _serialize_part_for_form(product)}, 200

    @auth_required("admin")
    def patch(self, product_id: str):
        product = Product.query.filter_by(pid=product_id).first()
        if product is None:
            inventory_ns.abort(404, "Part not found.")

        try:
            payload, image_file = _parse_create_part_request(allow_empty_vendor_prices=True)
            product = _update_part(product, payload, image_file)
        except ValueError as error:
            inventory_ns.abort(400, str(error))

        return {"product": _serialize_part_for_form(product)}, 200
