from app import db


class CustomerInvoice(db.Model):
    """Bill / dispatch note.

    Multiple invoices per order support partial fulfillment.
    """

    __tablename__ = "customer_invoices"

    cinv_id      = db.Column(db.String, primary_key=True)
    coid         = db.Column(db.String, db.ForeignKey("customer_orders.coid"), nullable=False)
    created_by   = db.Column(db.String, db.ForeignKey("users.uid"),            nullable=False)
    invoice_date = db.Column(db.Date,   nullable=False)
    status       = db.Column(db.String)  # Unpaid / PartiallyPaid / Paid
    total_amount = db.Column(db.Numeric(10, 2))

    # ── Relationships ─────────────────────────────────────────────
    customer_order = db.relationship("CustomerOrder",  back_populates="invoices")
    creator        = db.relationship("User",           back_populates="customer_invoices")
    details        = db.relationship("CustomerInvDetail", back_populates="customer_invoice", lazy="dynamic",
                                     cascade="all, delete-orphan")
    payments       = db.relationship("Payment",        back_populates="customer_invoice", lazy="dynamic")
    dispatches     = db.relationship("Dispatch",       back_populates="customer_invoice", lazy="dynamic")
    returns        = db.relationship("CustomerReturn", back_populates="customer_invoice", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<CustomerInvoice {self.cinv_id}>"


class CustomerInvDetail(db.Model):
    """Individual line items sold on a customer invoice."""

    __tablename__ = "customer_inv_details"

    cdetail_id    = db.Column(db.String, primary_key=True)
    cinv_id       = db.Column(db.String,  db.ForeignKey("customer_invoices.cinv_id"), nullable=False)
    skuid         = db.Column(db.String,  db.ForeignKey("skus.skuid"),                nullable=False)
    ordered_qty   = db.Column(db.Integer)
    delivered_qty = db.Column(db.Integer)         # May be less for partial fulfillment
    sale_price    = db.Column(db.Numeric(10, 2))  # Locked at time of invoice
    amount        = db.Column(db.Numeric(10, 2))

    # ── Relationships ─────────────────────────────────────────────
    customer_invoice = db.relationship("CustomerInvoice", back_populates="details")
    sku              = db.relationship("SKU",             back_populates="customer_inv_details")

    def __repr__(self) -> str:
        return f"<CustomerInvDetail {self.cdetail_id}>"
