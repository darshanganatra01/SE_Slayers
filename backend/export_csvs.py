import os
import json
import csv
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models.product import Product
from app.models.vendor import Vendor, VendorProduct
from app.models.sku import SKU


def export_csvs():
    app = create_app("development")
    with app.app_context():
        # Export Product.csv
        products = Product.query.all()
        product_path = os.path.join(app.root_path, 'static', 'Product.csv')
        with open(product_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['PID', 'PName', 'Category'])
            for p in products:
                writer.writerow([p.pid, p.pname, p.category])
        print(f"Exported {len(products)} rows to Product.csv")

        # Export Vendor.csv
        vendors = Vendor.query.all()
        vendor_path = os.path.join(app.root_path, 'static', 'Vendor.csv')
        with open(vendor_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['VID', 'VendorName', 'VendorPrefix', 'Location', 'Contact', 'Email'])
            for v in vendors:
                writer.writerow([v.vid, v.vendor_name, v.vendor_prefix, v.location, v.contact, v.email])
        print(f"Exported {len(vendors)} rows to Vendor.csv")

        # Export VendorProduct.csv
        vendor_products = VendorProduct.query.all()
        vendor_product_path = os.path.join(app.root_path, 'static', 'VendorProduct.csv')
        with open(vendor_product_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['VPID', 'VID', 'PID'])
            for vp in vendor_products:
                writer.writerow([vp.vpid, vp.vid, vp.pid])
        print(f"Exported {len(vendor_products)} rows to VendorProduct.csv")

        # Export SKU_table_2.csv
        skus = SKU.query.all()
        sku_path = os.path.join(app.root_path, 'static', 'SKU_table_2.csv')
        with open(sku_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'SKU ID', 'VendorProduct_ID', 'UnitMeasurementBuy', 'LotSizeBuy', 
                'Current_Buy', 'UnitMeasurementSell', 'LotSizeSell', 
                'Current_Sell', 'Specs_JSON', 'Threshold'
            ])
            for s in skus:
                specs_str = json.dumps(s.specs) if s.specs else "{}"
                # Format the numeric values or leave blank
                current_buy = f"{s.current_buy_rate:.2f}" if s.current_buy_rate is not None else ""
                current_sell = f"{s.current_sell_rate:.2f}" if s.current_sell_rate is not None else ""
                
                writer.writerow([
                    s.skuid, s.vpid, s.unit_measurement_buy, s.lot_size_buy,
                    current_buy, s.unit_measurement_sell, s.lot_size_sell,
                    current_sell, specs_str, s.threshold
                ])
        print(f"Exported {len(skus)} rows to SKU_table_2.csv")

if __name__ == "__main__":
    export_csvs()
