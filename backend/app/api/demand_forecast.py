"""
Demand-forecast API — lightweight item-level demand prediction using
statsforecast AutoETS (zero-shot exponential smoothing, no training).

Reads 30-day synthetic order data from CSV, aggregates daily demand per SKU,
forecasts 14 days ahead, and returns enriched results with stockout estimates.
"""

from __future__ import annotations

import csv
import math
import os
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

FORECAST_HORIZON = 14  # days ahead


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

            sku_map[skuid] = {
                "product_name": pname,
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


def _run_forecast(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Aggregate daily demand per SKU, run AutoETS forecast, return
    {skuid: DataFrame(ds, y | AutoETS)}.
    """
    # Aggregate: sum quantity per (skuid, order_date)
    daily = (
        df.groupby(["skuid", "order_date"])["quantity"]
        .sum()
        .reset_index()
        .rename(columns={"skuid": "unique_id", "order_date": "ds", "quantity": "y"})
    )
    daily["unique_id"] = daily["unique_id"].astype(str)

    # Fill missing dates with 0 for each SKU
    all_dates = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    filled_frames = []
    for uid in daily["unique_id"].unique():
        sku_df = daily[daily["unique_id"] == uid].set_index("ds").reindex(all_dates, fill_value=0).reset_index()
        sku_df.columns = ["ds", "unique_id_orig", "y"]
        sku_df["unique_id"] = uid
        # If reindex replaced unique_id, fix it
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
    forecast_df = sf.predict(h=FORECAST_HORIZON)
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
            sku_map = _load_product_map()
            order_df = _load_order_data()
            forecast_results = _run_forecast(order_df)
        except Exception as e:
            return {"error": str(e)}, 500

        forecasts = []
        for skuid, data in forecast_results.items():
            hist_df = data["historical"]
            pred_df = data["predicted"]

            meta = sku_map.get(skuid, {
                "product_name": f"SKU-{skuid}",
                "category": "Unknown",
                "stock_qty": 0,
                "threshold": 0,
                "sell_rate": 0,
            })

            # Historical series
            historical = [
                {"date": row["ds"].strftime("%Y-%m-%d"), "qty": max(0, round(row["y"]))}
                for _, row in hist_df.iterrows()
            ]

            # Predicted series — clamp negatives to 0
            predicted = [
                {"date": row["ds"].strftime("%Y-%m-%d"), "qty": max(0, round(row["AutoETS"]))}
                for _, row in pred_df.iterrows()
            ]

            total_predicted = sum(p["qty"] for p in predicted)
            avg_daily = round(total_predicted / FORECAST_HORIZON, 1) if FORECAST_HORIZON > 0 else 0

            stock = meta["stock_qty"]
            if avg_daily > 0:
                days_until_stockout = math.floor(stock / avg_daily)
            else:
                days_until_stockout = 999  # effectively infinite

            restock_alert = days_until_stockout <= FORECAST_HORIZON

            forecasts.append({
                "skuid": skuid,
                "product_name": meta["product_name"],
                "category": meta["category"],
                "historical": historical,
                "predicted": predicted,
                "total_predicted_14d": total_predicted,
                "avg_daily_predicted": avg_daily,
                "current_stock": stock,
                "threshold": meta["threshold"],
                "sell_rate": meta["sell_rate"],
                "days_until_stockout": days_until_stockout,
                "restock_alert": restock_alert,
            })

        # Sort by urgency (restock alerts first, then by days_until_stockout)
        forecasts.sort(key=lambda x: (not x["restock_alert"], x["days_until_stockout"]))

        return {
            "forecasts": forecasts,
            "forecast_horizon_days": FORECAST_HORIZON,
            "generated_at": datetime.now().isoformat(),
        }, 200
