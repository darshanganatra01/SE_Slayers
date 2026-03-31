from app import db


class Product(db.Model):
    """Master dictionary of all items."""

    __tablename__ = "products"

    pid      = db.Column(db.String, primary_key=True)
    pname    = db.Column(db.String, nullable=False)
    category = db.Column(db.String)

    # ── Relationships ─────────────────────────────────────────────
    vendor_products = db.relationship("VendorProduct", back_populates="product", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Product {self.pid} – {self.pname}>"
