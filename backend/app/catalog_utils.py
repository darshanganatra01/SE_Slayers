from __future__ import annotations

from pathlib import Path


PRODUCT_IMAGE_DIR = Path(__file__).resolve().parent / "static" / "product-images"


def ensure_product_image_dir() -> Path:
    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    return PRODUCT_IMAGE_DIR


def product_image_url(image_filename: str | None) -> str | None:
    if not image_filename:
        return None
    return f"/api/inventory/product-images/{image_filename}"


def legacy_product_image_path(product_name: str | None) -> str:
    normalized_name = str(product_name or "").strip() or "Product"
    return f"@/customer_dashboard/customer_assets/{normalized_name}.png".replace("G. I.", "GI")
