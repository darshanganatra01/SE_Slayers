from app import db


class CustomerReturn(db.Model):
    """Records goods returned by a customer.

    Linked to originating invoice.
    """

    __tablename__ = "customer_returns"

    c_return_id  = db.Column(db.String, primary_key=True)
    cinv_id      = db.Column(db.String, db.ForeignKey("customer_invoices.cinv_id"), nullable=False)
    initiated_by = db.Column(db.String, db.ForeignKey("users.uid"),                 nullable=False)
    return_date  = db.Column(db.Date,   nullable=False)
    reason       = db.Column(db.String)
    status       = db.Column(db.String)  # Pending / Processed / Refunded

    # ── Relationships ─────────────────────────────────────────────
    customer_invoice = db.relationship("CustomerInvoice", back_populates="returns")
    initiator        = db.relationship("User",            back_populates="customer_returns")
    details          = db.relationship("CustomerReturnDetail", back_populates="customer_return", lazy="dynamic",
                                       cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CustomerReturn {self.c_return_id}>"


class CustomerReturnDetail(db.Model):
    """Line items of a customer return.

    Processing triggers a positive StockAdjustment.
    """

    __tablename__ = "customer_return_details"

    cr_detail_id  = db.Column(db.String, primary_key=True)
    c_return_id   = db.Column(db.String,  db.ForeignKey("customer_returns.c_return_id"), nullable=False)
    skuid         = db.Column(db.String,  db.ForeignKey("skus.skuid"),                   nullable=False)
    return_qty    = db.Column(db.Integer, nullable=False)
    refund_amount = db.Column(db.Numeric(10, 2))

    # ── Relationships ─────────────────────────────────────────────
    customer_return = db.relationship("CustomerReturn", back_populates="details")
    sku             = db.relationship("SKU",            back_populates="customer_return_details")

    def __repr__(self) -> str:
        return f"<CustomerReturnDetail {self.cr_detail_id}>"
