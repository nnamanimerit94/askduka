"""End-to-end HTTP tests for AskDuka's internal catalog API.

Requires ASKDUKA_TEST_DATABASE_URL pointing to a disposable Neon branch.
The database must contain the AskDuka schema. The test transaction is
rolled back after each run, leaving no persistent test business/catalog.
"""
import os
from urllib.parse import urlparse

import pytest


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="No dedicated test database")
def test_admin_http_catalog_round_trip(monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from backend.app.admin_app import app
    from backend.app.catalog_api import db_session

    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    dbname = urlparse(url).path.lstrip("/")
    if dbname != "askduka_test":
        pytest.fail("Refusing writes outside dedicated askduka_test database")
    engine = create_engine(url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    app.dependency_overrides[db_session] = lambda: session
    monkeypatch.setenv("ASKDUKA_ADMIN_API_KEY", "local-test-secret")
    client = TestClient(app)
    headers = {"X-Admin-Key": "local-test-secret"}
    try:
        create = client.post("/admin/businesses", headers=headers, json={"name": "Test Hair Store"})
        assert create.status_code == 201, create.text
        business_id = create.json()["id"]
        save = client.post(
            f"/admin/businesses/{business_id}/catalog",
            headers=headers,
            json={"filename": "prices.txt", "content": "Wig: NGN 50000\nDelivery: 2 days"},
        )
        assert save.status_code == 201, save.text
        assert save.json()["lines_saved"] == 2
        fetch = client.get(f"/admin/businesses/{business_id}/catalog", headers=headers)
        assert fetch.status_code == 200, fetch.text
        assert fetch.json()["lines"] == ["Wig: NGN 50000", "Delivery: 2 days"]
        assert client.get(f"/admin/businesses/{business_id}/catalog").status_code == 401
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()
