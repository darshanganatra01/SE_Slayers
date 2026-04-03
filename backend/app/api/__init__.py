from flask import Blueprint
from flask_restx import Api

# ── Blueprint that hosts the entire REST API ──────────────────────
api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(
    api_bp,
    version="1.0",
    title="SE Slayers API",
    description="Backend API for the SE Slayers application",
    doc="/docs",                       # Swagger UI at /api/docs
)

# ── Import & register namespaces ──────────────────────────────────
from app.api.auth import auth_ns       # noqa: E402
from app.api.health import health_ns   # noqa: E402
from app.api.customer_portal.customer_portal import customer_ns
from app.api.internal_portal.internal_portal import internal_ns

api.add_namespace(auth_ns)
api.add_namespace(health_ns)
api.add_namespace(customer_ns)
api.add_namespace(internal_ns)
from app.api.inventory import inventory_ns  # noqa: E402


api.add_namespace(inventory_ns)
