import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import config_by_name

# ── Extensions (created here, initialised in create_app) ──────────
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name: str | None = None) -> Flask:
    """Application factory."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # ── Initialise extensions ─────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # ── Register API blueprint ────────────────────────────────────
    from app.api import api_bp
    app.register_blueprint(api_bp)

    @app.cli.command("seed-auth-users")
    def seed_auth_users_command():
        from app.seeds import seed_auth_users

        seeded = seed_auth_users()
        print("Seeded auth users:")
        print(f"  admin: {seeded['admin']['email']} / password123")
        print(f"  customer: {seeded['customer']['email']} / password123")

    @app.cli.command("seed-catalog")
    def seed_catalog_command():
        from app.catalog_seeds import seed_catalog_from_csv

        seeded = seed_catalog_from_csv()
        print("Seeded catalog data:")
        print(f"  products: {seeded['products']}")
        print(f"  vendors: {seeded['vendors']}")
        print(f"  vendor_products: {seeded['vendor_products']}")
        print(f"  skus: {seeded['skus']}")

    # ── Import models so Alembic can detect them ──────────────────
    from app import models  # noqa: F401

    return app
