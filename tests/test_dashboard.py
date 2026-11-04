from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.catalog_api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_dashboard_renders_without_database():
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "Register a business" in response.text
    assert "Save catalog" in response.text
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_dashboard_does_not_disable_admin_auth(monkeypatch):
    monkeypatch.setenv("ASKDUKA_ADMIN_API_KEY", "expected-key")
    response = client.post("/admin/businesses", json={"name": "Demo Store"})
    assert response.status_code == 401
