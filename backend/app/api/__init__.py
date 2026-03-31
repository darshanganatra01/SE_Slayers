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
from app.api.health import health_ns   # noqa: E402

api.add_namespace(health_ns)
