"""
Demand-forecast API — lightweight item-level demand prediction using
statsforecast AutoETS (zero-shot exponential smoothing, no training).

Reads 30-day synthetic order data from CSV, aggregates daily demand per SKU,
forecasts 7 days ahead, and returns enriched results with stockout estimates.
"""

from __future__ import annotations

import csv
import math
import os
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
from flask_restx import Namespace, Resource
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

demand_forecast_ns = Namespace(
    "demand-forecast",
    description="Item demand prediction for inventory planning",
)

# ── Paths ─────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CSV_PATH = os.path.join(_BASE_DIR, "Seed_values", "fake_order_data.csv")
_SKU_CSV  = os.path.join(_BASE_DIR, "Seed_values", "SKU_table_2.csv")
_PROD_CSV = os.path.join(_BASE_DIR, "Seed_values", "Product.csv")

FORECAST_HORIZON = 7  # days ahead


# ── Helpers ───────────────────────────────────────────────────────────

def _load_product_map() -> dict:
    """Build skuid -> {product_name, category, stock_qty, threshold} from seed CSVs."""
    # 1. Load products:  PID -> (PName, Category)
    products: dict[str, tuple[str, str]] = {}
    with open(_PROD_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            products[row["PID"].strip()] = (row["PName"].strip(), row["Category"].strip())

    # 2. Load SKUs and resolve product via VendorProduct mapping
    #    SKU CSV has VendorProduct_ID which maps to a product.
    #    The Vendor.csv/VendorProduct.csv mapping is simple: vpid -> pid.
    #    For seed data the VendorProduct_ID in SKU CSV == vpid in VendorProduct.csv.
    vp_csv = os.path.join(_BASE_DIR, "Seed_values", "VendorProduct.csv")
    vp_to_pid: dict[str, str] = {}
    with open(vp_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            vp_to_pid[row["VPID"].strip()] = row["PID"].strip()

    sku_map: dict[str, dict] = {}
    with open(_SKU_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            skuid = row["SKU ID"].strip()
            vpid = row["VendorProduct_ID"].strip()
            pid = vp_to_pid.get(vpid, "")
            pname, category = products.get(pid, (f"SKU-{skuid}", "Unknown"))

            specs_str = row.get("Specs_JSON", "{}").strip()
            try:
                specs_dict = json.loads(specs_str) if specs_str else {}
                specs_joined = ", ".join(str(v) for v in specs_dict.values() if v)
            except Exception:
                specs_joined = ""

            sku_map[skuid] = {
                "product_name": pname,
                "specs": specs_joined,
                "category": category,
                "stock_qty": int(row.get("stock_qty", 0) or 0),
                "threshold": int(row.get("Threshold", 0) or 0),
                "sell_rate": float(row.get("Current_Sell", 0) or 0),
            }
    return sku_map


def _load_order_data() -> pd.DataFrame:
    """Load synthetic order CSV into a DataFrame."""
    df = pd.read_csv(_CSV_PATH, parse_dates=["order_date"])
    return df


def _run_forecast(df: pd.DataFrame, sku_map: dict, horizon: int = 7) -> dict[str, pd.DataFrame]:
    """
    Aggregate daily demand per SKU, run AutoETS forecast, return
    {skuid: DataFrame(ds, y | AutoETS)}.
    """
    # Set fixed temporal anchor
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=29)
    all_dates = pd.date_range(start_date, end_date, freq="D")
    
    # Filter historical data strictly to the last 30 days
    df = df[(df["order_date"].dt.date >= start_date) & (df["order_date"].dt.date <= end_date)]

    # Aggregate: sum quantity per (skuid, order_date)
    daily = (
        df.groupby(["skuid", "order_date"])["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"skuid": "unique_id", "order_date": "ds", "quantity": "y"})
    )
    daily["unique_id"] = daily["unique_id"].astype(str)

    # 1. The "Silent SKU" Data Drop
    filled_frames = []
    
    # Pre-group the daily data by unique_id to optimize searches
    if not daily.empty:
        daily_grouped = dict(tuple(daily.groupby("unique_id")))
    else:
        daily_grouped = {}

    for uid in sku_map.keys():
        uid_str = str(uid)
        if uid_str in daily_grouped:
            sku_df = daily_grouped[uid_str].set_index("ds").reindex(all_dates, fill_value=0).reset_index()
            sku_df = sku_df.rename(columns={"index": "ds"})
        else:
            sku_df = pd.DataFrame({"ds": all_dates, "y": 0.0})

        sku_df["unique_id"] = uid_str
        sku_df = sku_df[["unique_id", "ds", "y"]]
        filled_frames.append(sku_df)

    full_df = pd.concat(filled_frames, ignore_index=True)
    full_df["y"] = full_df["y"].astype(float)

    # Run StatsForecast
    sf = StatsForecast(
        models=[AutoETS(season_length=7)],
        freq="D",
        n_jobs=1,
    )
    sf.fit(full_df)
    forecast_df = sf.predict(h=horizon)
    forecast_df = forecast_df.reset_index()

    # Split results by SKU
    results: dict[str, dict] = {}
    for skuid in full_df["unique_id"].unique():
        hist = full_df[full_df["unique_id"] == skuid][["ds", "y"]].copy()
        pred = forecast_df[forecast_df["unique_id"] == skuid][["ds", "AutoETS"]].copy()
        results[skuid] = {"historical": hist, "predicted": pred}

    return results


# ── Endpoint ──────────────────────────────────────────────────────────

@demand_forecast_ns.route("/predict")
class DemandPredictResource(Resource):
    def get(self):
        """Run demand forecast and return predictions for all SKUs."""
        try:
            from app.models.sku import SKU
            
            sku_map = _load_product_map()
            live_skus = SKU.query.all()
            max_lead_time = 7
            for s in live_skus:
                if s.skuid in sku_map:
                    sku_map[s.skuid]["stock_qty"] = s.stock_qty or 0
                    sku_map[s.skuid]["threshold"] = s.threshold or 0
                    
                    lt = 7
                    is_default_lt = True
                    try:
                        if s.vendor_product and s.vendor_product.vendor and s.vendor_product.vendor.lead_time is not None:
                            lt = s.vendor_product.vendor.lead_time
                            is_default_lt = False
                    except Exception:
                        pass
                        
                    sku_map[s.skuid]["lead_time"] = lt
                    sku_map[s.skuid]["is_default_lt"] = is_default_lt
                    if lt > max_lead_time:
                        max_lead_time = lt
                    
            order_df = _load_order_data()
            forecast_results = _run_forecast(order_df, sku_map, horizon=max_lead_time)
        except Exception as e:
            return {"error": str(e)}, 500

        forecasts = []
        for skuid, data in forecast_results.items():
            hist_df = data["historical"]
            pred_df = data["predicted"]

            meta = sku_map.get(skuid, {
                "product_name": f"SKU-{skuid}",
                "category": "Unknown",
                "specs": "",
                "stock_qty": 0,
                "threshold": 0,
                "sell_rate": 0,
            })

            # Historical series
            historical = [
                {"date": row["ds"].strftime("%Y-%m-%d"), "qty": max(0, round(row["y"]))}
                for _, row in hist_df.iterrows()
            ]

            # For Frontend charts: Strictly 7 days!
            pred_df_7d = pred_df.head(7)
            predicted_7d = [
                {"date": row["ds"].strftime("%Y-%m-%d"), "qty": max(0, round(row["AutoETS"]))}
                for _, row in pred_df_7d.iterrows()
            ]
            total_predicted_7d = sum(p["qty"] for p in predicted_7d)

            # For stockout math: strictly up to lead_time
            lead_time = meta.get("lead_time", 7)
            pred_df_lt = pred_df.head(lead_time)
            
            total_predicted_lt = sum(max(0, round(row["AutoETS"])) for _, row in pred_df_lt.iterrows())
            avg_daily_lt = round(total_predicted_lt / lead_time, 1) if lead_time > 0 else 0

            stock = meta["stock_qty"]
            threshold = meta["threshold"]

            if total_predicted_lt == 0:
                days_until_stockout = 9999
            elif avg_daily_lt > 0:
                days_until_stockout = math.floor(stock / avg_daily_lt)
            else:
                days_until_stockout = 9999

            restock_alert = (stock - total_predicted_lt) <= threshold or days_until_stockout <= lead_time

            is_default_lt = meta.get("is_default_lt", True)
            lead_time_display = f"{lead_time}*" if is_default_lt else str(lead_time)

            forecasts.append({
                "skuid": skuid,
                "product_name": meta["product_name"],
                "specs": meta["specs"],
                "category": meta["category"],
                "historical": historical,
                "predicted": predicted_7d,
                "total_predicted_7d": total_predicted_7d,
                "avg_daily_predicted": avg_daily_lt,
                "current_stock": stock,
                "threshold": threshold,
                "sell_rate": meta["sell_rate"],
                "days_until_stockout": days_until_stockout,
                "restock_alert": restock_alert,
                "lead_time_display": lead_time_display,
            })

        # Sort by urgency (restock alerts first, then by days_until_stockout)
        forecasts.sort(key=lambda x: (not x["restock_alert"], x["days_until_stockout"]))

        return {
            "forecasts": forecasts,
            "forecast_horizon_days": FORECAST_HORIZON,
            "generated_at": datetime.now().isoformat(),
        }, 200


def update_all_sku_thresholds(app):
    """Background service to recalculate mathematical database SKU thresholds via ATS forecast."""
    with app.app_context():
        from app.models.sku import SKU
        from app.models.customer_order import CustomerOrder
        from app.models.customer_order_detail import CustomerOrderDetail
        from app.models.packing_slip import PackingSlip
        from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
        from app import db
        import math

        # 1. Map SKUs and find global maximum lead time
        sku_map = _load_product_map()
        live_skus = db.session.query(SKU).all()
        max_lead_time = 7
        for s in live_skus:
            if s.skuid in sku_map:
                lt = 7
                try:
                    if s.vendor_product and s.vendor_product.vendor and s.vendor_product.vendor.lead_time is not None:
                        lt = s.vendor_product.vendor.lead_time
                except Exception:
                    pass
                sku_map[s.skuid]["lead_time"] = lt
                if lt > max_lead_time:
                    max_lead_time = lt
                    
        order_df = _load_order_data()
        forecast_results = _run_forecast(order_df, sku_map, horizon=max_lead_time)

        # 2. Get unfulfilled quantities directly from open DB orders
        open_orders = db.session.query(CustomerOrder).filter(
            CustomerOrder.status.notin_(["Completed", "Cancelled"])
        ).all()
        open_coid_list = [o.coid for o in open_orders]

        unfulfilled_map = defaultdict(int)

        if open_coid_list:
            ord_details = db.session.query(CustomerOrderDetail).filter(CustomerOrderDetail.coid.in_(open_coid_list)).all()
            for d in ord_details:
                unfulfilled_map[d.skuid] += d.quantity

            # Subtract officially shipped numbers from the backlog list
            inv_details = db.session.query(CustomerInvDetail).join(
                CustomerInvoice, CustomerInvDetail.cinv_id == CustomerInvoice.cinv_id
            ).join(
                PackingSlip, CustomerInvoice.pslip_id == PackingSlip.pslip_id
            ).filter(
                PackingSlip.coid.in_(open_coid_list)
            ).all()

            for idetail in inv_details:
                if idetail.delivered_qty:
                    unfulfilled_map[idetail.skuid] -= idetail.delivered_qty

        # 3. Apply Reorder Point Math and Save
        for sku in live_skus:
            f_data = forecast_results.get(sku.skuid)
            predicted_horizon = 0
            
            meta = sku_map.get(sku.skuid, {})
            lead_time = meta.get("lead_time", 7)
            
            if f_data is not None:
                pred_df = f_data["predicted"].head(lead_time)
                predicted_horizon = sum(max(0, round(row["AutoETS"])) for _, row in pred_df.iterrows())

            backlog = unfulfilled_map.get(sku.skuid, 0)
            
            # Reorder Point logic: ROP = LeadTimeDemand (Predicted + Backlog) + SafetyStock (20%)
            new_threshold = math.ceil((predicted_horizon + backlog) * 1.2)
            sku.threshold = new_threshold

        db.session.commit()

