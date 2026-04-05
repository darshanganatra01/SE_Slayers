from flask import request, jsonify
from flask_restx import Namespace, Resource
from app import db
from app.models.vendor import Vendor, VendorProduct
from app.models.product import Product
from app.models.sku import SKU
from app.api.ai_feature.tasks import process_vendor_pdf_task
import os
import tempfile

from app.auth import AuthError, auth_required

ai_ns = Namespace("ai-feature", description="AI PDF Data Extraction Features")

@ai_ns.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return {"message": error.message}, error.status_code

@ai_ns.route("/vendors")
class AIVendors(Resource):
    @auth_required("admin")
    def get(self):
        vendors = Vendor.query.all()
        return [{"vid": v.vid, "vendor_name": v.vendor_name} for v in vendors]

@ai_ns.route("/upload")
class AIUpload(Resource):
    @auth_required("admin")
    def post(self):
        if "pdf" not in request.files:
            return {"error": "Missing pdf file"}, 400
        vendor_id = request.form.get("vendor_id")
        if not vendor_id:
            return {"error": "Missing vendor_id"}, 400

        pdf_file = request.files["pdf"]
        
        # Save temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"vendor_{vendor_id}_{os.urandom(8).hex()}.pdf")
        pdf_file.save(temp_path)

        # Trigger celery task
        task = process_vendor_pdf_task.apply_async(args=[vendor_id, temp_path])
        return {"job_id": task.id}, 202

@ai_ns.route("/status/<job_id>")
class AIStatus(Resource):
    @auth_required("admin")
    def get(self, job_id):
        task = process_vendor_pdf_task.AsyncResult(job_id)
        if task.state == 'PENDING':
            return {"state": task.state, "message": "Job is pending..."}
        elif task.state == 'PROGRESS':
            return {"state": task.state, "message": task.info.get('message', '')}
        elif task.state == 'SUCCESS':
            result = task.result
            if result.get("status") == "error":
                return {"state": "FAILURE", "message": result.get("message")}
            return {"state": "SUCCESS", "matches": result.get("matches")}
        else:
            # FAILURE or other
            return {"state": task.state, "message": str(task.info)}

@ai_ns.route("/confirm")
class AIConfirm(Resource):
    @auth_required("admin")
    def post(self):
        data = request.json
        approved_matches = data.get("approved_matches", [])
        
        updates = 0
        missing_skus = []
        for match in approved_matches:
            sku_id = match.get("sku_id")
            new_price = match.get("price")
            if sku_id and new_price is not None:
                sku = SKU.query.get(sku_id)
                if not sku:
                    missing_skus.append(sku_id)
                    continue
                if float(sku.current_buy_rate or 0) != float(new_price):
                    sku.current_buy_rate = float(new_price)
                    updates += 1
                    
        if missing_skus:
            db.session.rollback()
            return {"error": f"Validation failed: The following SKU IDs do not exist: {missing_skus}"}, 400
            
        db.session.commit()
        return {"message": f"Successfully updated {updates} SKUs", "updates": updates}
