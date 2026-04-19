import pytest
import os

# Set environmental variable before app imports to force SQLite in TestingConfig
os.environ["TEST_DATABASE_URL"] = "sqlite://"

@pytest.fixture()
def app():
    from app import create_app, db
    
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY="test-secret",
        JWT_EXPIRATION_HOURS=1,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def auth_headers(app):
    from app.seeds import seed_auth_users
    from app.auth import issue_token
    from app.models.user import User
    
    with app.app_context():
        seed_auth_users()
        admin = User.query.filter_by(email="owner@metrohardware.com").first()
        token = issue_token(admin)
        return {"Authorization": f"Bearer {token}"}
