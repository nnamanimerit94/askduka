"""HTTP-level checks for the owner-only app with no database connection."""
from fastapi.testclient import TestClient

from backend.app.owner_app import app


def test_owner_only_http_surface():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["service"] == "askduka-owner-private"
        for path in ("/admin", "/admin/dashboard", "/docs", "/openapi.json"):
            assert client.get(path).status_code == 404
        assert client.get("/api/businesses").status_code == 401
        assert client.get("/api/auth/me").status_code == 401
        assert client.post("/api/auth/logout").status_code == 401


def test_registration_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ASKDUKA_ENABLE_OWNER_SIGNUP", raising=False)
    # The disabled check is inside the endpoint; dependency injection can
    # still construct the DB dependency, so override it with an inert session.
    from backend.app.owner_auth_api import db_session

    def fake_db():
        yield object()

    app.dependency_overrides[db_session] = fake_db
    try:
        with TestClient(app) as client:
            response = client.post("/api/auth/register-business", json={
                "email": "owner@example.com",
                "password": "long safe password",
                "business_name": "Demo Shop",
            })
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
