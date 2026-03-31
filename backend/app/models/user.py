from app import db


class User(db.Model):
    """Staff accounts.

    UID is referenced as CreatedBy / RecordedBy / AdjustedBy /
    InitiatedBy / DispatchedBy across all operational tables.
    """

    __tablename__ = "users"

    uid           = db.Column(db.String, primary_key=True)
    full_name     = db.Column(db.String, nullable=False)
    role          = db.Column(db.String, nullable=False)            # Admin / Manager / Sales / Store
    email         = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    is_active     = db.Column(db.Boolean, default=True)

    # ── Relationships ─────────────────────────────────────────────
    customers           = db.relationship("Customer",        back_populates="user",            lazy="dynamic")
    vendor_orders       = db.relationship("VendorOrder",     back_populates="creator",         lazy="dynamic")
    customer_orders     = db.relationship("CustomerOrder",   back_populates="creator",         lazy="dynamic")
    customer_invoices   = db.relationship("CustomerInvoice", back_populates="creator",         lazy="dynamic")
    payments            = db.relationship("Payment",         back_populates="recorder",        lazy="dynamic")
    dispatches          = db.relationship("Dispatch",        back_populates="dispatcher",      lazy="dynamic")
    vendor_returns      = db.relationship("VendorReturn",    back_populates="initiator",       lazy="dynamic")
    customer_returns    = db.relationship("CustomerReturn",  back_populates="initiator",       lazy="dynamic")
    stock_adjustments   = db.relationship("StockAdjustment", back_populates="adjuster",        lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.uid} – {self.full_name}>"
