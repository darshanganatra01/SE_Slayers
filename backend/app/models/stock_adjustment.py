from app import db


class StockAdjustment(db.Model):
    """Immutable audit log for every stock change outside normal buy/sell flows."""

    __tablename__ = "stock_adjustments"

    adj_id      = db.Column(db.String, primary_key=True)
    skuid       = db.Column(db.String, db.ForeignKey("skus.skuid"), nullable=False)
    adjusted_by = db.Column(db.String, db.ForeignKey("users.uid"),  nullable=False)
    adj_date    = db.Column(db.Date,   nullable=False)
    delta       = db.Column(db.Integer, nullable=False)   # +ve = added, −ve = removed
    reason      = db.Column(db.String)                     # Damage / Write-off / Opening Stock / Manual Correction / Return
    ref_doc_id  = db.Column(db.String)                     # Optional FK to VendorReturn or CustomerReturn

    # ── Relationships ─────────────────────────────────────────────
    sku      = db.relationship("SKU",  back_populates="stock_adjustments")
    adjuster = db.relationship("User", back_populates="stock_adjustments")

    def __repr__(self) -> str:
        return f"<StockAdjustment {self.adj_id} Δ{self.delta}>"
