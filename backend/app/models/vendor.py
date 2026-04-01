from app import db


class Vendor(db.Model):
    """Central directory of all suppliers."""

    __tablename__ = "vendors"

    vid           = db.Column(db.String, primary_key=True)
    vendor_name   = db.Column(db.String, nullable=False)
    vendor_prefix = db.Column(db.String)   # Vendor-specific prefix
    location      = db.Column(db.String)
    contact       = db.Column(db.String)
    email         = db.Column(db.String)

    # ── Relationships ─────────────────────────────────────────────
    vendor_products = db.relationship("VendorProduct", back_populates="vendor", lazy="dynamic")
    vendor_orders   = db.relationship("VendorOrder",   back_populates="vendor", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Vendor {self.vid} – {self.vendor_name}>"


class VendorProduct(db.Model):
    """Maps which vendor sells which product, with one or more SKU variants."""

    __tablename__ = "vendor_products"

    vpid = db.Column(db.String, primary_key=True)
    vid  = db.Column(db.String, db.ForeignKey("vendors.vid"),  nullable=False)
    pid  = db.Column(db.String, db.ForeignKey("products.pid"), nullable=False)

    # ── Relationships ─────────────────────────────────────────────
    vendor  = db.relationship("Vendor",  back_populates="vendor_products")
    product = db.relationship("Product", back_populates="vendor_products")
    skus    = db.relationship("SKU",     back_populates="vendor_product", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<VendorProduct {self.vpid}>"
