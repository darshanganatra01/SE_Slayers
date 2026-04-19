"""
Generate 30 days of synthetic order-detail data for demand forecasting.

Output: Seed_values/fake_order_data.csv
Columns: codid, coid, skuid, quantity, amount, order_date

The data mirrors the `customer_order_details` table but adds `order_date`
(pulled from the parent order) so the forecast service can aggregate by day.
"""

import csv
import random
import os
from datetime import date, timedelta

# ── SKU catalog (subset from SKU_table_2.csv) ────────────────────────
# Format: (skuid, sell_rate, product_name, category, demand_profile)
# demand_profile: "high" = daily orders, "medium" = every 2-3 days, "low" = sporadic
SKUS = [
    # Pipes — high volume consumables
    ("47", 36.0,   "SS Step Nipple 0.5\" x 6\"",           "Pipes",    "high"),
    ("48", 50.4,   "SS Step Nipple 0.75\" x 6\"",          "Pipes",    "high"),
    ("49", 51.6,   "SS Step Nipple 1\" x 7\"",             "Pipes",    "high"),
    ("50", 67.2,   "SS Step Nipple 1.25\" x 7\"",          "Pipes",    "high"),
    ("51", 79.2,   "SS Step Nipple 1.5\" x 7\"",           "Pipes",    "medium"),
    ("52", 52.8,   "SS Reduce Nipple 1\" x 0.75\" x 7\"",  "Pipes",    "high"),
    ("53", 69.6,   "SS Reduce Nipple 1.25\" x 1\" x 7\"",  "Pipes",    "medium"),
    ("67", 27.6,   "GI Step Nipple 0.5\" x 6\"",           "Pipes",    "high"),
    ("68", 31.2,   "GI Step Nipple 0.75\" x 6\"",          "Pipes",    "high"),
    ("69", 44.4,   "GI Step Nipple 1\" x 7\"",             "Pipes",    "medium"),

    # Fittings — medium volume
    ("1",  23.4,   "Sprinkler Clamp 2.5mm 63mm",           "Fittings", "medium"),
    ("2",  24.6,   "Sprinkler Clamp 2.5mm 75mm",           "Fittings", "medium"),
    ("3",  27.0,   "Sprinkler Clamp 2.5mm 90mm",           "Fittings", "medium"),
    ("30", 360.0,  "Hose Clip Light 1.5\"",                "Fittings", "medium"),
    ("31", 276.0,  "Hose Clip Light 2\"",                  "Fittings", "medium"),
    ("42", 78.0,   "Borcap 3x1",                           "Fittings", "low"),
    ("43", 128.4,  "Borcap 4x1",                           "Fittings", "low"),

    # Sprinkler rubber rings — seasonal burst
    ("133", 4.2,   "Sprinkler Rubber Ring Heavy 63mm",      "Fittings", "seasonal"),
    ("134", 5.4,   "Sprinkler Rubber Ring Heavy 75mm",      "Fittings", "seasonal"),
    ("135", 7.8,   "Sprinkler Rubber Ring Heavy 90mm",      "Fittings", "seasonal"),

    # Drip irrigation — medium
    ("146", 2.4,   "Drip Irrigation Lateral Cock 12mm",     "Fittings", "medium"),
    ("147", 3.6,   "Drip Irrigation Lateral Cock 16mm",     "Fittings", "medium"),

    # Butterfly valves — expensive, low frequency
    ("77",  1231.2, "Butterfly Valve SGIN 50mm Lever",      "Fittings", "low"),
    ("78",  1398.0, "Butterfly Valve SGIN 65mm Lever",      "Fittings", "low"),
    ("86",  4866.0, "Butterfly Valve SGIN 100mm Gear",      "Fittings", "low"),

    # Sprinkler pipe fittings
    ("113", 82.8,  "Sprinkler Pipe F+M Pioneer 63mm",       "Fittings", "medium"),
    ("114", 96.0,  "Sprinkler Pipe F+M Pioneer 75mm",       "Fittings", "medium"),
    ("115", 120.0, "Sprinkler Pipe F+M Pioneer 90mm",       "Fittings", "low"),
]

# ── Demand profiles ──────────────────────────────────────────────────
def get_daily_qty(profile: str, day_of_week: int, day_idx: int) -> int:
    """
    Return a random quantity for this SKU on a given day.
    Returns 0 if no order on this day.
    day_of_week: 0=Mon ... 6=Sun
    day_idx: 0..29 (day within the 30-day window)
    """
    # Weekends have lower demand (B2B)
    weekend_factor = 0.3 if day_of_week >= 5 else 1.0

    if profile == "high":
        # Order almost every day, qty 5–30
        if random.random() < 0.85 * weekend_factor:
            return random.randint(5, 30)
        return 0

    elif profile == "medium":
        # Order every 2-3 days, qty 3–15
        if random.random() < 0.50 * weekend_factor:
            return random.randint(3, 15)
        return 0

    elif profile == "low":
        # Sporadic — once a week or less, qty 1–5
        if random.random() < 0.15 * weekend_factor:
            return random.randint(1, 5)
        return 0

    elif profile == "seasonal":
        # Burst in the middle of the month (days 10-20), quiet otherwise
        if 8 <= day_idx <= 22:
            if random.random() < 0.70 * weekend_factor:
                return random.randint(20, 80)
            return 0
        else:
            if random.random() < 0.10 * weekend_factor:
                return random.randint(5, 15)
            return 0

    return 0


def generate():
    random.seed(42)  # reproducible

    today = date(2026, 4, 8)
    start = today - timedelta(days=29)  # 30 days inclusive

    rows = []
    codid_counter = 1
    coid_counter = 1

    for day_idx in range(30):
        current_date = start + timedelta(days=day_idx)
        dow = current_date.weekday()

        # Each day can have multiple orders from different customers
        # Group SKU orders into a few "orders" per day
        day_items = []
        for skuid, sell_rate, pname, cat, profile in SKUS:
            qty = get_daily_qty(profile, dow, day_idx)
            if qty > 0:
                day_items.append((skuid, qty, sell_rate))

        if not day_items:
            continue

        # Split day_items into 1-4 "orders"
        random.shuffle(day_items)
        num_orders = min(len(day_items), random.randint(1, 4))
        chunk_size = max(1, len(day_items) // num_orders)

        for order_chunk_idx in range(num_orders):
            start_i = order_chunk_idx * chunk_size
            end_i = start_i + chunk_size if order_chunk_idx < num_orders - 1 else len(day_items)
            chunk = day_items[start_i:end_i]

            if not chunk:
                continue

            coid = f"FAKE-CO-{coid_counter:04d}"
            coid_counter += 1

            for skuid, qty, sell_rate in chunk:
                codid = f"FAKE-COD-{codid_counter:05d}"
                codid_counter += 1
                amount = round(qty * sell_rate, 2)
                rows.append({
                    "codid": codid,
                    "coid": coid,
                    "skuid": skuid,
                    "quantity": qty,
                    "amount": amount,
                    "order_date": current_date.isoformat(),
                })

    # Write CSV
    out_path = os.path.join(os.path.dirname(__file__), "Seed_values", "fake_order_data.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["codid", "coid", "skuid", "quantity", "amount", "order_date"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows across {coid_counter - 1} fake orders → {out_path}")
    return out_path


if __name__ == "__main__":
    generate()
