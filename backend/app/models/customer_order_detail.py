from app import db


class CustomerOrderDetail(db.Model):
    """Line items of a Sales Order."""

    __tablename__ = "customer_order_details"

    codid    = db.Column(db.String, primary_key=True)
    coid     = db.Column(db.String, db.ForeignKey("customer_orders.coid"), nullable=False)
    skuid    = db.Column(db.String, db.ForeignKey("skus.skuid"),            nullable=False)
    quantity = db.Column(db.Integer)

    # ── Relationships ─────────────────────────────────────────────
    customer_order = db.relationship("CustomerOrder", back_populates="details")
    sku            = db.relationship("SKU",           back_populates="customer_order_details")

    def __repr__(self) -> str:
        return f"<CustomerOrderDetail {self.codid}>"
