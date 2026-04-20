from flask import Response, request
from flask_restx import Namespace, Resource, fields

from app import db
from app.auth import AuthError, auth_required, issue_token, register_customer, serialize_user
from app.models.user import User

auth_ns = Namespace("auth", description="Authentication endpoints")

login_model = auth_ns.model(
    "LoginRequest",
    {
        "email": fields.String(required=True),
        "password": fields.String(required=True),
    },
)

register_model = auth_ns.model(
    "RegisterRequest",
    {
        "full_name": fields.String(required=True),
        "email": fields.String(required=True),
        "password": fields.String(required=True),
        "contact": fields.String(required=False),
        "location": fields.String(required=False),
        "pincode": fields.Integer(required=False),
    },
)


def _validate_login_payload(payload: dict) -> tuple[str, str]:
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        raise AuthError("Email and password are required.", status_code=400)

    return email, password


def _validate_register_payload(payload: dict) -> tuple[str, str, str, str | None, str | None, int | None]:
    full_name = (payload.get("full_name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    contact = payload.get("contact")
    location = payload.get("location")
    pincode = payload.get("pincode")

    if not full_name:
        raise AuthError("Full name is required.", status_code=400)
    if not email:
        raise AuthError("Email is required.", status_code=400)
    if not password:
        raise AuthError("Password is required.", status_code=400)
    
    # Optional pincode conversion if sent as string
    if pincode is not None and not isinstance(pincode, int):
        try:
            pincode = int(pincode)
        except (ValueError, TypeError):
            pincode = None

    return full_name, email, password, contact, location, pincode


@auth_ns.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return {"message": error.message}, error.status_code


@auth_ns.route("/login")
class LoginResource(Resource):
    @auth_ns.expect(login_model, validate=False)
    def post(self):
        payload = request.get_json(silent=True) or {}
        email, password = _validate_login_payload(payload)
        user = User.query.filter_by(email=email, is_active=True).first()

        if user is None or not user.check_password(password):
            raise AuthError("Invalid email or password.", status_code=401)

        return {
            "token": issue_token(user),
            "user": serialize_user(user),
        }, 200


@auth_ns.route("/register")
class RegisterResource(Resource):
    @auth_ns.expect(register_model, validate=False)
    def post(self):
        payload = request.get_json(silent=True) or {}
        full_name, email, password, contact, location, pincode = _validate_register_payload(payload)
        user = register_customer(
            full_name=full_name,
            email=email,
            password=password,
            contact=contact,
            location=location,
            pincode=pincode,
        )
        db.session.add(user)
        db.session.commit()

        return {
            "token": issue_token(user),
            "user": serialize_user(user),
        }, 201


@auth_ns.route("/me")
class MeResource(Resource):
    @auth_required()
    def get(self):
        from app.auth import get_current_user

        return {"user": serialize_user(get_current_user())}, 200

@auth_ns.route('/swagger.yaml')
@auth_ns.hide
class SwaggerYaml(Resource):
    def get(self):
        from app.api import api
        try:
            import yaml
        except ModuleNotFoundError:
            return {"message": "PyYAML is required to generate swagger.yaml."}, 503

        # Convert schema to YAML string
        yaml_data = yaml.dump(api.__schema__, default_flow_style=False)
        return Response(yaml_data, mimetype='text/yaml')
