from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import wraps
from uuid import uuid4

import jwt
from flask import current_app, g, request

from app.models.customer import Customer
from app.models.user import User


class AuthError(Exception):
    """Raised when authentication or authorization fails."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def generate_user_id() -> str:
    return f"USR-{uuid4().hex[:8].upper()}"


def generate_customer_id() -> str:
    return f"CUS-{uuid4().hex[:8].upper()}"


def issue_token(user: User) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=current_app.config["JWT_EXPIRATION_HOURS"])
    payload = {
        "sub": user.uid,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Your session has expired. Please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid authentication token.") from exc


def get_token_from_request() -> str:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        raise AuthError("Missing authentication token.")

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("Authorization header must use Bearer token format.")
    return token


def get_current_user() -> User:
    if getattr(g, "current_user", None) is not None:
        return g.current_user

    token = get_token_from_request()
    payload = decode_token(token)
    user = User.query.filter_by(uid=payload["sub"], is_active=True).first()
    if user is None:
        raise AuthError("Authenticated user was not found.", status_code=401)

    g.current_user = user
    g.jwt_payload = payload
    return user


def auth_required(*roles: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if roles and user.role not in roles:
                raise AuthError("You do not have access to this resource.", status_code=403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def serialize_user(user: User) -> dict:
    customer = user.customer_profile
    return {
        "uid": user.uid,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "customer": (
            {
                "cid": customer.cid,
                "customer_name": customer.customer_name,
                "email": customer.email,
                "contact": customer.contact,
            }
            if customer is not None
            else None
        ),
    }


def register_customer(*, full_name: str, email: str, password: str, contact: str | None = None, location: str | None = None, pincode: int | None = None) -> User:
    email_normalized = email.strip().lower()
    if User.query.filter_by(email=email_normalized).first() is not None:
        raise AuthError("An account with this email already exists.", status_code=409)

    user = User(
        uid=generate_user_id(),
        full_name=full_name.strip(),
        email=email_normalized,
        role=User.ROLE_CUSTOMER,
        is_active=True,
    )
    user.set_password(password)

    customer = Customer(
        cid=generate_customer_id(),
        uid=user.uid,
        customer_name=user.full_name,
        contact=contact.strip() if contact else None,
        email=email_normalized,
        location=location.strip() if location else None,
        pincode=pincode,
    )
    user.customer_profile = customer
    return user
