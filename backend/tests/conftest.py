import pytest

from app import create_app, db


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
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
