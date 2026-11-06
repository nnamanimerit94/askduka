import uuid
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.owner_auth_api import router, db_session


def fake_db():
    yield object()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[db_session] = fake_db
client = TestClient(app)


def test_login_returns_token_and_invalid_credentials_are_generic():
    with patch("backend.app.owner_auth_api.login_owner", return_value="opaque-token"):
        response = client.post("/api/auth/login", json={"email": "owner@example.com", "password": "long secure password"})
    assert response.status_code == 200
    assert response.json()["access_token"] == "opaque-token"
    assert response.json()["token"] == "opaque-token"
    with patch("backend.app.owner_auth_api.login_owner", return_value=None):
        response = client.post("/api/auth/login", json={"email": "owner@example.com", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_me_requires_valid_session():
    assert client.get("/api/auth/me").status_code == 401
    owner_id = uuid.uuid4()
    with patch("backend.app.owner_auth_api.current_owner_id", return_value=owner_id):
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer opaque-token"})
    assert response.status_code == 200
    assert response.json()["owner_id"] == str(owner_id)


def test_logout_revokes_session():
    with patch("backend.app.owner_auth_api.current_owner_id", return_value=uuid.uuid4()), patch("backend.app.owner_auth_api.logout_owner", return_value=True) as revoke:
        response = client.post("/api/auth/logout", headers={"Authorization": "Bearer opaque-token"})
    assert response.status_code == 200
    revoke.assert_called_once()


def test_invalid_session_cannot_logout():
    with patch("backend.app.owner_auth_api.current_owner_id", return_value=None):
        response = client.post("/api/auth/logout", headers={"Authorization": "Bearer expired"})
    assert response.status_code == 401
