from app import db


class VendorOrder(db.Model):
    """Purchase Order (PO) raised to a vendor."""

    __tablename__ = "vendor_orders"

    void       = db.Column(db.String, primary_key=True)
    vid        = db.Column(db.String, db.ForeignKey("vendors.vid"), nullable=False)
    created_by = db.Column(db.String, db.ForeignKey("users.uid"),   nullable=False)
    order_date = db.Column(db.Date,   nullable=False)
    status     = db.Column(db.String)  # Draft / Confirmed / PartiallyReceived / Completed / Cancelled

    # ── Relationships ─────────────────────────────────────────────
    vendor   = db.relationship("Vendor", back_populates="vendor_orders")
    creator  = db.relationship("User",   back_populates="vendor_orders")
    details  = db.relationship("VendorOrderDetail", back_populates="vendor_order", lazy="dynamic",
                               cascade="all, delete-orphan")
    invoices = db.relationship("VendorInvoice",     back_populates="vendor_order", lazy="dynamic",
                               cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<VendorOrder {self.void}>"


class VendorOrderDetail(db.Model):
    """Line items of a Purchase Order."""

    __tablename__ = "vendor_order_details"

    vo_detail_id = db.Column(db.String, primary_key=True)
    void         = db.Column(db.String,  db.ForeignKey("vendor_orders.void"), nullable=False)
    skuid        = db.Column(db.String,  db.ForeignKey("skus.skuid"),         nullable=False)
    ordered_qty  = db.Column(db.Integer, nullable=False)
    agree_price  = db.Column(db.Numeric(10, 2))   # Agreed price at time of PO

    # ── Relationships ─────────────────────────────────────────────
    vendor_order = db.relationship("VendorOrder", back_populates="details")
    sku          = db.relationship("SKU",         back_populates="vendor_order_details")

    def __repr__(self) -> str:
        return f"<VendorOrderDetail {self.vo_detail_id}>"
