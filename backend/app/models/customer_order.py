from app import db


class CustomerOrder(db.Model):
    """Sales Order.

    Priority inheritance from Customer.Category is enforced at
    application layer.
    """

    __tablename__ = "customer_orders"

    coid       = db.Column(db.String, primary_key=True)
    cid        = db.Column(db.String, db.ForeignKey("customers.cid"), nullable=False)
    created_by = db.Column(db.String, db.ForeignKey("users.uid"),     nullable=False)
    order_date = db.Column(db.Date,   nullable=False)
    status       = db.Column(db.String)  # Draft / Confirmed / PartiallyFulfilled / Completed / Cancelled
    priority     = db.Column(db.String)  # High / Medium / Low — inherits Customer.Category by default
    total_amount = db.Column(db.Numeric(10, 2))

    # ── Relationships ─────────────────────────────────────────────
    customer = db.relationship("Customer",        back_populates="orders")
    creator  = db.relationship("User",            back_populates="customer_orders")
    details  = db.relationship("CustomerOrderDetail", back_populates="customer_order", lazy="dynamic",
                               cascade="all, delete-orphan")
    invoices = db.relationship("CustomerInvoice", back_populates="customer_order", lazy="dynamic",
                               cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CustomerOrder {self.coid}>"
