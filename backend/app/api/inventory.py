from __future__ import annotations

from collections import OrderedDict
from datetime import date
from decimal import Decimal

from app import db
from flask_restx import Namespace, Resource

from app.auth import AuthError, auth_required
from app.models.product import Product
from app.models.sku import SKU
from app.models.vendor import VendorProduct

inventory_ns = Namespace("inventory", description="Inventory endpoints")


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


def _build_spec_display(specs: dict | None) -> tuple[str, str]:
    if not isinstance(specs, dict) or not specs:
        return "-", ""

    values = [str(value).strip() for value in specs.values() if str(value).strip()]
    if not values:
        return "-", ""

    size = values[-1]
    detail_values = values[:-1]
    details = " · ".join(detail_values)
    return size, details


def _portfolio_chip_status(status: str) -> str:
    if status == "instock":
        return "ok"
    return status


def _status_rank(status: str) -> int:
    ranks = {"instock": 3, "low": 2, "out": 1}
    return ranks.get(status, 0)


def _build_portfolio_products() -> tuple[list[dict], dict[str, dict]]:
    rows = (
        db.session.query(
            Product.pid,
            Product.pname,
            Product.category,
            SKU.skuid,
            SKU.specs,
            SKU.stock_qty,
            SKU.threshold,
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

        status = _stock_status(row.stock_qty, row.threshold)
        size, spec = _build_spec_display(row.specs)
        chip_status = _portfolio_chip_status(status)

        chip_index = next(
            (index for index, item in enumerate(grouped_products[product_key]["sizes"]) if item["label"] == size),
            None,
        )
        if chip_index is None:
            grouped_products[product_key]["sizes"].append({"label": size, "status": chip_status})
        else:
            existing = grouped_products[product_key]["sizes"][chip_index]["status"]
            if _status_rank(status) > _status_rank("instock" if existing == "ok" else existing):
                grouped_products[product_key]["sizes"][chip_index]["status"] = chip_status

        popup_data = detail_map[product_key]
        size_index = popup_data["_size_index"]
        if size not in size_index:
            popup_data["rows"].append(
                {
                    "size": size,
                    "dim": spec,
                    "stock": row.stock_qty or 0,
                    "maxStock": row.threshold or 0,
                    "status": chip_status,
                }
            )
            size_index[size] = len(popup_data["rows"]) - 1
        else:
            detail_row = popup_data["rows"][size_index[size]]
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
            )
            .order_by(Product.pname.asc(), SKU.skuid.asc())
            .all()
        )

        parts = []
        total_inventory_value = Decimal("0.00")

        for row in rows:
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
