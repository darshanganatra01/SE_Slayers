from app import create_app, db
import urllib.request
import json
import urllib.error
from app.models.customer import Customer

app = create_app()
with app.app_context():
    cust = Customer.query.first()
    if not cust:
        print("No customers in DB!")
    else:
        url = 'http://127.0.0.1:5000/api/customer/orders'
        data = {
            "cid": cust.cid,
            "items": [{"skuId": "1", "quantity": 1}]
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as response:
                print("Status", response.status)
                print("Body", response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print("Error Status", e.code)
            print("Error Body", e.read().decode('utf-8'))
        except Exception as e:
            print("Exception", e)
