from celery_app import celery_app
from app import create_app, db
from app.api.ai_feature.services import (
    get_api_keys, create_clients, validate_vendor_pdf, extract_tables, 
    match_skus, validate
)
from app.models.vendor import Vendor, VendorProduct
import os

@celery_app.task(bind=True)
def process_vendor_pdf_task(self, vendor_id, file_path):
    # Setup App Context for Database access
    app = create_app("development")
    with app.app_context():
        try:
            self.update_state(state='PROGRESS', meta={'message': 'Loading Vendor and DB records...'})
            
            vendor = Vendor.query.get(vendor_id)
            if not vendor:
                return {"status": "error", "message": "Vendor not found."}
                
            vendor_products = VendorProduct.query.filter_by(vid=vendor_id).all()
            enriched_skus = []
            for vp in vendor_products:
                for sku in vp.skus:
                    enriched_skus.append({
                        "sku_id": sku.skuid,
                        "product_name": vp.product.pname,
                        "specs": str(sku.specs) if sku.specs else "{}",
                        "current_buy_rate": sku.current_buy_rate
                    })

            if not enriched_skus:
                return {"status": "error", "message": "No SKUs found for this vendor."}

            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            api_keys = get_api_keys()
            clients = create_clients(api_keys)

            # Step 1: Pre-flight validation (Option 3)
            self.update_state(state='PROGRESS', meta={'message': 'Validating PDF Vendor Match...'})
            try:
                is_valid_vendor = validate_vendor_pdf(pdf_bytes, vendor.vendor_name, clients)
            except Exception as e:
                return {"status": "error", "message": f"Validation failed: {str(e)}"}

            if not is_valid_vendor:
                return {"status": "error", "message": f"Pre-check failed: This document does not appear to be a price list for {vendor.vendor_name}."}

            # Step 2: Extraction
            self.update_state(state='PROGRESS', meta={'message': 'Extracting Tables...'})
            tables = extract_tables(pdf_bytes, clients)
            if not tables:
                return {"status": "error", "message": "No tables extracted from PDF."}
                
            # Step 3: Matching
            self.update_state(state='PROGRESS', meta={'message': 'Matching SKUs with Prices...'})
            matches = match_skus(tables, enriched_skus, clients)
            
            # Step 4: Validation & Retry Loop
            self.update_state(state='PROGRESS', meta={'message': 'Validating Price Changes...'})
            validated = validate(matches, enriched_skus)
            
            anomalies = [m for m in validated if m.get('change_pct') and abs(m.get('change_pct')) > 50]
            if anomalies:
                self.update_state(state='PROGRESS', meta={'message': f'Self-correcting {len(anomalies)} anomalies...'})
                # Re-run and overwrite the anomaly matches
                from app.api.ai_feature.services import retry_anomalies
                retried_matches = retry_anomalies(tables, anomalies, enriched_skus, clients)
                
                # Merge retried matches, replacing old anomalies in `matches`
                if retried_matches:
                    retry_map = {str(m['sku_id']): m for m in retried_matches}
                    for i, original_match in enumerate(matches):
                        sk_id = str(original_match.get('sku_id', '')).replace('SKU ', '').strip()
                        if sk_id in retry_map:
                            matches[i] = retry_map[sk_id]
                    # Re-validate with the merged data
                    validated = validate(matches, enriched_skus)
            
            # Cleanup temp file
            try:
                os.remove(file_path)
            except:
                pass
                
            return {"status": "success", "matches": validated}
            
        except Exception as e:
            return {"status": "error", "message": f"An internal error occurred: {str(e)}"}
