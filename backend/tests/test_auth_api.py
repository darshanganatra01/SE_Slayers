from datetime import UTC, datetime, timedelta

import jwt

from app import db
from app.auth import issue_token
from app.models.customer import Customer
from app.models.user import User
from app.seeds import seed_auth_users


def test_seed_auth_users_creates_admin_and_customer(app):
    with app.app_context():
        seeded = seed_auth_users()
        admin = User.query.filter_by(email=seeded["admin"]["email"]).first()
        customer = User.query.filter_by(email=seeded["customer"]["email"]).first()
        customer_profile = Customer.query.filter_by(uid=customer.uid).first()

        assert admin is not None
        assert admin.role == User.ROLE_ADMIN
        assert customer is not None
        assert customer.role == User.ROLE_CUSTOMER
        assert customer_profile is not None


def test_login_returns_token_and_admin_role(client, app):
    with app.app_context():
        seed_auth_users()

    response = client.post(
        "/api/auth/login",
        json={"email": "owner@metrohardware.com", "password": "password123"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["token"]
    assert payload["user"]["role"] == "admin"
    assert payload["user"]["customer"] is None


def test_login_accepts_customer_and_preserves_customer_profile(client, app):
    with app.app_context():
        seed_auth_users()

    response = client.post(
        "/api/auth/login",
        json={"email": "CUSTOMER@EXAMPLE.COM", "password": "password123"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["user"]["role"] == "customer"
    assert payload["user"]["customer"]["cid"]
    assert payload["user"]["customer"]["email"] == "customer@example.com"
    assert payload["user"]["customer"]["contact"] == "9999999999"


def test_login_rejects_invalid_password_with_generic_message(client, app):
    with app.app_context():
        seed_auth_users()

    response = client.post(
        "/api/auth/login",
        json={"email": "owner@metrohardware.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid email or password."


def test_login_rejects_inactive_user(client, app):
    with app.app_context():
        user = User(
            uid="USR-INACTIVE",
            full_name="Inactive User",
            email="inactive@example.com",
            role=User.ROLE_CUSTOMER,
            is_active=False,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid email or password."


def test_login_requires_email_and_password(client):
    response = client.post("/api/auth/login", json={"email": "", "password": ""})

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."


def test_register_creates_customer_user_and_profile(client, app):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Buyer",
            "email": "Alice@Example.com",
            "password": "password123",
            "contact": "8888888888",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["user"]["role"] == "customer"
    assert payload["user"]["customer"]["contact"] == "8888888888"

    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        customer = Customer.query.filter_by(uid=user.uid).first()
        assert user is not None
        assert customer is not None
        assert customer.customer_name == "Alice Buyer"


def test_register_rejects_duplicate_email(client, app):
    with app.app_context():
        seed_auth_users()

    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Copy User",
            "email": "customer@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["message"] == "An account with this email already exists."


def test_register_requires_minimum_fields(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "", "email": "", "password": ""},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Full name is required."


def test_me_returns_current_user_for_valid_token(client, app):
    with app.app_context():
        seed_auth_users()
        user = User.query.filter_by(email="customer@example.com").first()
        token = issue_token(user)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "customer@example.com"
    assert response.get_json()["user"]["customer"]["cid"]


def test_me_requires_bearer_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.get_json()["message"] == "Missing authentication token."


def test_me_rejects_expired_token(client, app):
    with app.app_context():
        seed_auth_users()
        user = User.query.filter_by(email="customer@example.com").first()
        expired_token = jwt.encode(
            {
                "sub": user.uid,
                "role": user.role,
                "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
                "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
            },
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.get_json()["message"] == "Your session has expired. Please sign in again."
