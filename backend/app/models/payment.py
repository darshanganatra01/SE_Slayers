from app import db


class Payment(db.Model):
    """One payment event.

    Multiple payments per invoice support partial settlement.
    """

    __tablename__ = "payments"

    payment_id   = db.Column(db.String, primary_key=True)
    cinv_id      = db.Column(db.String, db.ForeignKey("customer_invoices.cinv_id"), nullable=False)
    recorded_by  = db.Column(db.String, db.ForeignKey("users.uid"),                 nullable=False)
    payment_date = db.Column(db.Date,   nullable=False)
    amount       = db.Column(db.Numeric(10, 2), nullable=False)
    method       = db.Column(db.String)  # Cash / UPI / Bank Transfer / Cheque
    reference    = db.Column(db.String)  # UTR, cheque number, or transaction ID
    notes        = db.Column(db.Text)

    # ── Relationships ─────────────────────────────────────────────
    customer_invoice = db.relationship("CustomerInvoice", back_populates="payments")
    recorder         = db.relationship("User",            back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment {self.payment_id} ₹{self.amount}>"
