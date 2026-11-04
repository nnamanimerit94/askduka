"""Tests that the internal admin app is separate from public preview."""
from fastapi.testclient import TestClient

from backend.app.admin_app import app as admin_app
from backend.app.preview import app as preview_app


def test_internal_admin_dashboard_available():
    response = TestClient(admin_app).get("/admin/dashboard")
    assert response.status_code == 200
    assert "Register a business" in response.text


def test_public_preview_does_not_expose_admin_dashboard():
    response = TestClient(preview_app).get("/admin/dashboard")
    assert response.status_code == 404


def test_internal_admin_does_not_expose_openapi_docs():
    client = TestClient(admin_app)
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
