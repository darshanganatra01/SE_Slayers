from app import db


class DeliveryReceipt(db.Model):
    """Customer confirmation of goods received for a given invoice.

    One receipt per invoice. Can be created by the customer or
    by an admin on behalf of the customer.
    """

    __tablename__ = "delivery_receipts"

    receipt_id    = db.Column(db.String, primary_key=True)
    cinv_id       = db.Column(db.String, db.ForeignKey("customer_invoices.cinv_id"), nullable=False)
    received_by   = db.Column(db.String, db.ForeignKey("users.uid"),                 nullable=False)
    received_date = db.Column(db.Date,   nullable=False)
    notes         = db.Column(db.Text)

    # ── Relationships ─────────────────────────────────────────────
    customer_invoice = db.relationship("CustomerInvoice", back_populates="delivery_receipts")
    receiver         = db.relationship("User",            back_populates="delivery_receipts")
    details          = db.relationship("DeliveryReceiptDetail", back_populates="delivery_receipt",
                                       lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DeliveryReceipt {self.receipt_id}>"


class DeliveryReceiptDetail(db.Model):
    """Line items confirming receipt of individual SKUs."""

    __tablename__ = "delivery_receipt_details"

    dr_detail_id  = db.Column(db.String, primary_key=True)
    receipt_id    = db.Column(db.String, db.ForeignKey("delivery_receipts.receipt_id"), nullable=False)
    skuid         = db.Column(db.String, db.ForeignKey("skus.skuid"),                  nullable=False)
    received_qty  = db.Column(db.Integer, nullable=False)
    condition     = db.Column(db.String)  # Good / Damaged / Wrong Item

    # ── Relationships ─────────────────────────────────────────────
    delivery_receipt = db.relationship("DeliveryReceipt", back_populates="details")
    sku              = db.relationship("SKU",             back_populates="delivery_receipt_details")

    def __repr__(self) -> str:
        return f"<DeliveryReceiptDetail {self.dr_detail_id}>"
