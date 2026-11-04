"""Catalog API authentication and validation tests (no live database required)."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.catalog_api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_admin_endpoints_require_key(monkeypatch):
    monkeypatch.setenv("ASKDUKA_ADMIN_API_KEY", "test-secret")
    response = client.post("/admin/businesses", json={"name": "Hair Shop"})
    assert response.status_code == 401


def test_invalid_key_is_rejected(monkeypatch):
    monkeypatch.setenv("ASKDUKA_ADMIN_API_KEY", "test-secret")
    response = client.post(
        "/admin/businesses",
        headers={"X-Admin-Key": "wrong"},
        json={"name": "Hair Shop"},
    )
    assert response.status_code == 401


def test_missing_server_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("ASKDUKA_ADMIN_API_KEY", raising=False)
    response = client.get(
        "/admin/businesses/00000000-0000-0000-0000-000000000000/catalog",
        headers={"X-Admin-Key": "anything"},
    )
    assert response.status_code == 401


def test_short_name_is_rejected_before_database_access(monkeypatch):
    monkeypatch.setenv("ASKDUKA_ADMIN_API_KEY", "test-secret")
    response = client.post(
        "/admin/businesses",
        headers={"X-Admin-Key": "test-secret"},
        json={"name": " "},
    )
    assert response.status_code == 422
