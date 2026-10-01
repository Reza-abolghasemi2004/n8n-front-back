import os
from pathlib import Path
import sys
import tempfile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models.user import AdminUser


@pytest.fixture(scope="session")
def postgres_url():
    """Provide a real PostgreSQL connection URI for the test session."""
    explicit_url = os.getenv("TEST_DATABASE_URL")
    if explicit_url:
        yield explicit_url
        return

    import pgserver

    tmp_dir = tempfile.mkdtemp(prefix="pg_test_")
    server = pgserver.get_server(tmp_dir)
    try:
        yield server.get_uri()
    finally:
        server.cleanup()


@pytest.fixture()
def app(postgres_url):
    test_app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": postgres_url,
            "SECRET_KEY": "test-secret-key",
            "N8N_BASE_URL": "http://n8n:5678",
            "N8N_API_KEY": "test-n8n-api-key",
            "N8N_WEBHOOK_PATH": "/webhook/project-intake",
        }
    )

    with test_app.app_context():
        db.drop_all()
        db.create_all()

        admin = AdminUser(
            username="admin",
            email="admin@example.com",
            full_name="Test Admin",
            is_active_user=True,
        )
        admin.set_password("StrongPass123!")
        db.session.add(admin)
        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    response = client.post(
        "/login",
        data={"identifier": "admin", "password": "StrongPass123!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return client
