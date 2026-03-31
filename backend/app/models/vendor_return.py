from app import db


class VendorReturn(db.Model):
    """Records goods being sent back to a vendor.

    Linked to the originating invoice.
    """

    __tablename__ = "vendor_returns"

    v_return_id  = db.Column(db.String, primary_key=True)
    inv_id       = db.Column(db.String, db.ForeignKey("vendor_invoices.inv_id"), nullable=False)
    initiated_by = db.Column(db.String, db.ForeignKey("users.uid"),              nullable=False)
    return_date  = db.Column(db.Date,   nullable=False)
    reason       = db.Column(db.String)
    status       = db.Column(db.String)  # Pending / Processed / Credited

    # ── Relationships ─────────────────────────────────────────────
    vendor_invoice = db.relationship("VendorInvoice", back_populates="returns")
    initiator      = db.relationship("User",          back_populates="vendor_returns")
    details        = db.relationship("VendorReturnDetail", back_populates="vendor_return", lazy="dynamic",
                                     cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<VendorReturn {self.v_return_id}>"


class VendorReturnDetail(db.Model):
    """Line items of a vendor return.

    Processing triggers a negative StockAdjustment.
    """

    __tablename__ = "vendor_return_details"

    vr_detail_id  = db.Column(db.String, primary_key=True)
    v_return_id   = db.Column(db.String,  db.ForeignKey("vendor_returns.v_return_id"), nullable=False)
    skuid         = db.Column(db.String,  db.ForeignKey("skus.skuid"),                 nullable=False)
    return_qty    = db.Column(db.Integer, nullable=False)
    credit_amount = db.Column(db.Numeric(10, 2))

    # ── Relationships ─────────────────────────────────────────────
    vendor_return = db.relationship("VendorReturn", back_populates="details")
    sku           = db.relationship("SKU",          back_populates="vendor_return_details")

    def __repr__(self) -> str:
        return f"<VendorReturnDetail {self.vr_detail_id}>"
