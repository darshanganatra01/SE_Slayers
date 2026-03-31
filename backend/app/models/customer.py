from app import db


class Customer(db.Model):
    """Central directory of all customers."""

    __tablename__ = "customers"

    cid           = db.Column(db.String, primary_key=True)
    uid           = db.Column(db.String, db.ForeignKey("users.uid"), nullable=False)
    customer_name = db.Column(db.String, nullable=False)
    category      = db.Column(db.String)   # Defines default priority: High / Medium / Low
    location      = db.Column(db.String)
    pincode       = db.Column(db.Integer)
    contact       = db.Column(db.String)
    email         = db.Column(db.String)

    # ── Relationships ─────────────────────────────────────────────
    user   = db.relationship("User",          back_populates="customers")
    orders = db.relationship("CustomerOrder", back_populates="customer", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Customer {self.cid} – {self.customer_name}>"
