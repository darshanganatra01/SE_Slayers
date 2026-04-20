import pytest
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app import db
from app.models.sku import SKU
from app.models.product import Product
from app.models.vendor import Vendor, VendorProduct
from app.models.customer_order import CustomerOrder
from app.models.customer_order_detail import CustomerOrderDetail
from app.models.customer_invoice import CustomerInvoice, CustomerInvDetail
from app.models.packing_slip import PackingSlip
from app.api.demand_forecast import update_all_sku_thresholds

# Using a fixed date for deterministic tests: Oct 1, 2023
MOCK_TODAY = datetime(2023, 10, 1)

@pytest.fixture
def frozen_time():
    """Mock datetime.today and datetime.now in the demand_forecast module."""
    with patch('app.api.demand_forecast.datetime') as mock_dt:
        mock_dt.today.return_value = MOCK_TODAY
        mock_dt.now.return_value = MOCK_TODAY
        # Keep side_effect to allow datetime(...) constructor calls
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt

def test_predict_empty_db(client, app, frozen_time):
    """Verify that the predict endpoint returns gracefully with an empty DB."""
    response = client.get("/api/demand-forecast/predict")
    assert response.status_code == 200
    data = response.get_json()
    assert "forecasts" in data
    assert len(data["forecasts"]) == 0
    assert data["forecast_horizon_days"] == 7

def test_predict_silent_skus(client, app, frozen_time):
    """Verify that SKUs with no history still appear in forecasts."""
    with app.app_context():
        p = Product(pid="P1", pname="Screw", category="Hardware")
        v = Vendor(vid="V1", vendor_name="Vendor1")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        s = SKU(skuid="S1", vpid="VP1", stock_qty=10, threshold=5, current_sell_rate=Decimal("1.00"))
        db.session.add_all([p, v, vp, s])
        db.session.commit()

    response = client.get("/api/demand-forecast/predict")
    assert response.status_code == 200
    data = response.get_json()
    
    assert len(data["forecasts"]) == 1
    forecast = data["forecasts"][0]
    assert forecast["skuid"] == "S1"
    assert forecast["total_predicted_7d"] == 0
    assert forecast["days_until_stockout"] == 9999
    assert forecast["restock_alert"] is False

def test_predict_historical_window(client, app, frozen_time):
    """Verify strictly filtering to only the last 30 days of orders."""
    with app.app_context():
        p = Product(pid="P1", pname="Screw")
        v = Vendor(vid="V1", vendor_name="V1")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        s = SKU(skuid="S1", vpid="VP1", stock_qty=100)
        db.session.add_all([p, v, vp, s])
        
        # Order outside window (31 days ago)
        o1 = CustomerOrder(coid="CO1", order_date=(MOCK_TODAY - timedelta(days=31)).date())
        d1 = CustomerOrderDetail(codid="D1", coid="CO1", skuid="S1", quantity=50)
        
        # Order inside window (5 days ago)
        o2 = CustomerOrder(coid="CO2", order_date=(MOCK_TODAY - timedelta(days=5)).date())
        d2 = CustomerOrderDetail(codid="D2", coid="CO2", skuid="S1", quantity=10)
        
        db.session.add_all([o1, d1, o2, d2])
        db.session.commit()

    response = client.get("/api/demand-forecast/predict")
    data = response.get_json()
    forecast = data["forecasts"][0]
    
    # Historical data should NOT include the order from 31 days ago
    # Wait, the code aggregates daily. In historical list, we should see Oct 1st - 29 days back.
    historical_qtys = [day["qty"] for day in forecast["historical"] if day["qty"] > 0]
    assert len(historical_qtys) == 1
    assert historical_qtys[0] == 10  # Only the order from 5 days ago

def test_predict_lead_time_handling(client, app, frozen_time):
    """Verify restock_alert logic with custom lead times."""
    with app.app_context():
        p = Product(pid="P1", pname="Fast-Seller")
        v = Vendor(vid="V1", vendor_name="V1", lead_time=10) # 10 days LT
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        # Stock: 20. Predicted demand: let's say it will be high.
        s = SKU(skuid="S1", vpid="VP1", stock_qty=20, threshold=5) 
        db.session.add_all([p, v, vp, s])
        
        # Consistent high demand: 5 per day for the last 30 days
        for i in range(30):
            order_date = (MOCK_TODAY - timedelta(days=i)).date()
            o = CustomerOrder(coid=f"O{i}", order_date=order_date)
            d = CustomerOrderDetail(codid=f"D{i}", coid=f"O{i}", skuid="S1", quantity=5)
            db.session.add_all([o, d])
        db.session.commit()

    response = client.get("/api/demand-forecast/predict")
    data = response.get_json()
    forecast = data["forecasts"][0]
    
    assert forecast["lead_time_display"] == "10"
    # Average daily should be ~5. 
    # Days until stockout = stock(20) / daily(5) = 4 days.
    # Since days_until_stockout (4) <= lead_time (10), restock_alert must be True.
    assert forecast["days_until_stockout"] <= 10
    assert forecast["restock_alert"] is True

def test_threshold_backlog_calc(app, frozen_time):
    """Verify background service backlog calculation (Ordered - Delivered)."""
    with app.app_context():
        p = Product(pid="P1", pname="Item")
        v = Vendor(vid="V1", vendor_name="V1")
        vp = VendorProduct(vpid="VP1", vid="V1", pid="P1")
        s = SKU(skuid="S1", vpid="VP1", threshold=0)
        db.session.add_all([p, v, vp, s])
        
        # Order 1: Partially delivered. Ordered 10, Shipped 4. Backlog = 6.
        o1 = CustomerOrder(coid="CO1", status="Confirmed", order_date=MOCK_TODAY.date())
        d1 = CustomerOrderDetail(codid="D1", coid="CO1", skuid="S1", quantity=10)
        ps1 = PackingSlip(pslip_id="PS1", coid="CO1")
        inv1 = CustomerInvoice(cinv_id="INV1", pslip_id="PS1")
        inv_d1 = CustomerInvDetail(cdetail_id="ID1", cinv_id="INV1", skuid="S1", delivered_qty=4)
        
        # Order 2: Not yet processed. Ordered 5. Backlog = 5.
        o2 = CustomerOrder(coid="CO2", status="Confirmed", order_date=MOCK_TODAY.date())
        d2 = CustomerOrderDetail(codid="D2", coid="CO2", skuid="S1", quantity=5)
        
        db.session.add_all([o1, d1, ps1, inv1, inv_d1, o2, d2])
        db.session.commit()

        # Update thresholds
        update_all_sku_thresholds(app)
        
        updated_s = SKU.query.get("S1")
        # predicted_horizon should be 0 (no historical data to forecast from)
        # backlog = (10 - 4) + 5 = 11
        # threshold = ceil((0 + 11) * 1.2) = ceil(13.2) = 14
        assert updated_s.threshold == 14

def test_threshold_status_filter(app, frozen_time):
    """Verify backlog excludes Completed and Cancelled orders."""
    with app.app_context():
        s = SKU(skuid="S1", vpid="VP1", threshold=0)
        db.session.add(s)
        
        # Completed order
        o1 = CustomerOrder(coid="CO1", status="Completed", order_date=MOCK_TODAY.date())
        d1 = CustomerOrderDetail(codid="D1", coid="CO1", skuid="S1", quantity=10)
        
        # Cancelled order
        o2 = CustomerOrder(coid="CO2", status="Cancelled", order_date=MOCK_TODAY.date())
        d2 = CustomerOrderDetail(codid="D2", coid="CO2", skuid="S1", quantity=10)
        
        db.session.add_all([o1, d1, o2, d2])
        db.session.commit()

        update_all_sku_thresholds(app)
        
        updated_s = SKU.query.get("S1")
        # backlog should be 0
        assert updated_s.threshold == 0
