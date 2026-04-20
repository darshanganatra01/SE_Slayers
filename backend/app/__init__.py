import os

from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect, text
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import config_by_name

# ── Extensions (created here, initialised in create_app) ──────────
db = SQLAlchemy()
migrate = Migrate()


def _ensure_schema_compatibility() -> None:
    """Apply small runtime compatibility fixes for existing databases.

    Some developer environments still have an older `products` table that was
    created before `image_filename` was introduced. `create_all()` will not add
    the new column to an existing table, and any ORM query that loads `Product`
    will fail until the schema is updated. We patch that column in a safe,
    idempotent way at startup so the app remains usable even before a manual
    Alembic upgrade is run.
    """

    inspector = inspect(db.engine)
    if "products" not in inspector.get_table_names():
        return

    product_columns = {column["name"] for column in inspector.get_columns("products")}
    if "image_filename" in product_columns:
        return

    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE products ADD COLUMN image_filename VARCHAR"))


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

    @app.cli.command("reset-db")
    def reset_db_command():
        from app.catalog_seeds import seed_catalog_from_csv
        from app.seeds import seed_auth_users
        
        print("Destroying entire database...")
        db.drop_all()
        print("Recreating clean tables...")
        db.create_all()
        
        print("Seeding fresh catalog...")
        seed_catalog_from_csv()
        
        print("Seeding default auth users...")
        seed_auth_users()
        print("Database completely reset and re-seeded successfully! You have a 100% fresh start.")

    # ── Import models so Alembic can detect them ──────────────────
    from app import models  # noqa: F401

    with app.app_context():
        _ensure_schema_compatibility()

    return app
