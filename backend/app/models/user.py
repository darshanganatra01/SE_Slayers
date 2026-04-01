from app import db
from werkzeug.security import check_password_hash, generate_password_hash


class User(db.Model):
    """System accounts for both business owners and customers."""

    ROLE_ADMIN = "admin"
    ROLE_CUSTOMER = "customer"
    ROLES = {ROLE_ADMIN, ROLE_CUSTOMER}

    __tablename__ = "users"

    uid           = db.Column(db.String, primary_key=True)
    full_name     = db.Column(db.String, nullable=False)
    role          = db.Column(db.String, nullable=False)            # admin / customer
    email         = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    is_active     = db.Column(db.Boolean, default=True)

    # ── Relationships ─────────────────────────────────────────────
    customer_profile    = db.relationship("Customer",        back_populates="user",            uselist=False)
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

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN

    @property
    def is_customer(self) -> bool:
        return self.role == self.ROLE_CUSTOMER
