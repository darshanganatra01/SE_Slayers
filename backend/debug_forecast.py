import sys
import os
sys.path.append(os.getcwd())

from app import create_app
app = create_app('development')

with app.app_context():
    from app.api.demand_forecast import DemandPredictResource
    res = DemandPredictResource()
    try:
        data, status = res.get()
        if status == 200:
            print("SUCCESS")
            print(f"Forecasts count: {len(data['forecasts'])}")
        else:
            print(f"ERROR: {status}")
            print(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
