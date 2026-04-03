from app import db


class SKU(db.Model):
    """Physical stock unit in godown.

    A VendorProduct may have multiple SKU variants.
    """

    __tablename__ = "skus"

    skuid                 = db.Column(db.String, primary_key=True)
    vpid                  = db.Column(db.String, db.ForeignKey("vendor_products.vpid"), nullable=False)
    unit_measurement_buy  = db.Column(db.Integer)
    lot_size_buy          = db.Column(db.Integer)
    current_buy_rate      = db.Column(db.Numeric(10, 2))
    unit_measurement_sell = db.Column(db.Integer)
    lot_size_sell         = db.Column(db.Integer)
    current_sell_rate     = db.Column(db.Numeric(10, 2))
    specs                 = db.Column(db.JSON)          # Item variations — size, color, grade, etc.
    stock_qty             = db.Column(db.Integer, default=0)
    threshold             = db.Column(db.Integer)        # Reorder level

    # ── Relationships ─────────────────────────────────────────────
    vendor_product          = db.relationship("VendorProduct",       back_populates="skus")
    vendor_order_details    = db.relationship("VendorOrderDetail",   back_populates="sku", lazy="dynamic")
    vendor_invoice_details  = db.relationship("VendorInvoiceDetail", back_populates="sku", lazy="dynamic")
    vendor_return_details   = db.relationship("VendorReturnDetail",  back_populates="sku", lazy="dynamic")
    customer_inv_details    = db.relationship("CustomerInvDetail",   back_populates="sku", lazy="dynamic")
    customer_order_details  = db.relationship("CustomerOrderDetail", back_populates="sku", lazy="dynamic")
    customer_return_details = db.relationship("CustomerReturnDetail",back_populates="sku", lazy="dynamic")
    packing_slip_details    = db.relationship("PackingSlipDetail",   back_populates="sku", lazy="dynamic")
    stock_adjustments       = db.relationship("StockAdjustment",     back_populates="sku", lazy="dynamic")
    delivery_receipt_details = db.relationship("DeliveryReceiptDetail", back_populates="sku", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<SKU {self.skuid} qty={self.stock_qty}>"
