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
