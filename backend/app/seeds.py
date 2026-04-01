from app import db
from app.auth import generate_customer_id, issue_token
from app.models.customer import Customer
from app.models.user import User


def seed_auth_users() -> dict:
    """Create or update dummy admin and customer users for testing."""

    db.create_all()

    admin_email = "owner@metrohardware.com"
    customer_email = "customer@example.com"
    default_password = "password123"

    admin = User.query.filter_by(email=admin_email).first()
    if admin is None:
        admin = User(
            uid="USR-ADMIN01",
            full_name="Metro Business Owner",
            email=admin_email,
            role=User.ROLE_ADMIN,
            is_active=True,
        )
        db.session.add(admin)
    admin.set_password(default_password)

    customer = User.query.filter_by(email=customer_email).first()
    if customer is None:
        customer = User(
            uid="USR-CUST01",
            full_name="Sample Customer",
            email=customer_email,
            role=User.ROLE_CUSTOMER,
            is_active=True,
        )
        db.session.add(customer)
    customer.set_password(default_password)

    customer_profile = Customer.query.filter_by(uid=customer.uid).first()
    if customer_profile is None:
        customer_profile = Customer(
            cid=generate_customer_id(),
            uid=customer.uid,
            customer_name=customer.full_name,
            email=customer.email,
            contact="9999999999",
        )
        db.session.add(customer_profile)
    else:
        customer_profile.customer_name = customer.full_name
        customer_profile.email = customer.email
        customer_profile.contact = "9999999999"

    db.session.commit()

    return {
        "admin": {
            "email": admin.email,
            "password": default_password,
            "token_preview": issue_token(admin)[:20],
        },
        "customer": {
            "email": customer.email,
            "password": default_password,
            "token_preview": issue_token(customer)[:20],
        },
    }
