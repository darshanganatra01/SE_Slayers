from app import db


class VendorInvoice(db.Model):
    """Delivery document from vendor.

    Multiple invoices per order support partial deliveries.
    """

    __tablename__ = "vendor_invoices"

    inv_id         = db.Column(db.String, primary_key=True)
    void           = db.Column(db.String, db.ForeignKey("vendor_orders.void"), nullable=False)
    invoice_date   = db.Column(db.Date,   nullable=False)
    vendor_inv_num = db.Column(db.String)  # Vendor-side invoice reference number

    # ── Relationships ─────────────────────────────────────────────
    vendor_order = db.relationship("VendorOrder",         back_populates="invoices")
    details      = db.relationship("VendorInvoiceDetail", back_populates="vendor_invoice", lazy="dynamic",
                                   cascade="all, delete-orphan")
    returns      = db.relationship("VendorReturn",        back_populates="vendor_invoice", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<VendorInvoice {self.inv_id}>"


class VendorInvoiceDetail(db.Model):
    """Line items of a vendor invoice.

    Price is historical and immutable after entry.
    """

    __tablename__ = "vendor_invoice_details"

    detail_id      = db.Column(db.String, primary_key=True)
    inv_id         = db.Column(db.String,  db.ForeignKey("vendor_invoices.inv_id"), nullable=False)
    skuid          = db.Column(db.String,  db.ForeignKey("skus.skuid"),             nullable=False)
    ordered_qty    = db.Column(db.Integer)
    arrived_qty    = db.Column(db.Integer)          # May differ from ordered — tracks shortfalls
    purchase_price = db.Column(db.Numeric(10, 2))   # Locked at time of invoice

    # ── Relationships ─────────────────────────────────────────────
    vendor_invoice = db.relationship("VendorInvoice", back_populates="details")
    sku            = db.relationship("SKU",           back_populates="vendor_invoice_details")

    def __repr__(self) -> str:
        return f"<VendorInvoiceDetail {self.detail_id}>"
