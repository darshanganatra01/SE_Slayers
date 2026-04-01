from app import db


class Dispatch(db.Model):
    """Records when and how goods leave the godown for a given invoice."""

    __tablename__ = "dispatches"

    dispatch_id   = db.Column(db.String, primary_key=True)
    cinv_id       = db.Column(db.String, db.ForeignKey("customer_invoices.cinv_id"), nullable=False)
    dispatched_by = db.Column(db.String, db.ForeignKey("users.uid"),                 nullable=False)
    dispatch_date = db.Column(db.Date,   nullable=False)
    carrier       = db.Column(db.String)
    status        = db.Column(db.String)  # Pending / Dispatched / Delivered

    # ── Relationships ─────────────────────────────────────────────
    customer_invoice = db.relationship("CustomerInvoice", back_populates="dispatches")
    dispatcher       = db.relationship("User",            back_populates="dispatches")

    def __repr__(self) -> str:
        return f"<Dispatch {self.dispatch_id}>"
