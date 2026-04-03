from app import db


class PackingSlip(db.Model):
    """Represents one packed batch from an order.
    
    Status moves to Shipped when invoice is created.
    """

    __tablename__ = "packing_slips"

    pslip_id    = db.Column(db.String, primary_key=True)
    coid        = db.Column(db.String, db.ForeignKey("customer_orders.coid"), nullable=False)
    packed_by   = db.Column(db.String, db.ForeignKey("users.uid"),            nullable=False)
    packed_date = db.Column(db.Date,   nullable=False)
    status      = db.Column(db.String)  # Packed / Shipped

    # ── Relationships ─────────────────────────────────────────────
    customer_order = db.relationship("CustomerOrder", back_populates="packing_slips")
    packer         = db.relationship("User",          back_populates="packing_slips")
    details        = db.relationship("PackingSlipDetail", back_populates="packing_slip", lazy="dynamic",
                                     cascade="all, delete-orphan")
    invoices       = db.relationship("CustomerInvoice", back_populates="packing_slip", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<PackingSlip {self.pslip_id}>"


class PackingSlipDetail(db.Model):
    """Line items in the packed batch.
    
    PackedQty must not exceed remaining unfulfilled qty from CustomerOrderDetail.
    """

    __tablename__ = "packing_slip_details"

    psd_id      = db.Column(db.String, primary_key=True)
    pslip_id    = db.Column(db.String, db.ForeignKey("packing_slips.pslip_id"), nullable=False)
    skuid       = db.Column(db.String, db.ForeignKey("skus.skuid"),             nullable=False)
    packed_qty  = db.Column(db.Integer, nullable=False)

    # ── Relationships ─────────────────────────────────────────────
    packing_slip = db.relationship("PackingSlip", back_populates="details")
    sku          = db.relationship("SKU",          back_populates="packing_slip_details")

    def __repr__(self) -> str:
        return f"<PackingSlipDetail {self.psd_id}>"
