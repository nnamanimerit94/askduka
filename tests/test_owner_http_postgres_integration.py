"""Real HTTP owner onboarding flow against a disposable PostgreSQL test DB."""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.models import Base, Business
from backend.app.db.owner_models import BusinessMembership, OwnerAccount
from backend.app.db.session_models import OwnerSession
from backend.app.owner_app import app
from backend.app.owner_auth_api import db_session


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL")
def test_owner_registration_login_business_and_logout_http(monkeypatch):
    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    assert url.split("?")[0].endswith("/askduka_test"), "Refusing non-test database"
    engine = create_engine(url)
    owner_id = business_id = None
    email = f"http-owner-{uuid.uuid4()}@example.com"

    def session_override():
        with Session(engine) as session:
            yield session

    try:
        Base.metadata.create_all(engine, tables=[
            Business.__table__, OwnerAccount.__table__,
            BusinessMembership.__table__, OwnerSession.__table__,
        ])
        app.dependency_overrides[db_session] = session_override
        monkeypatch.setenv("ASKDUKA_ENABLE_OWNER_SIGNUP", "true")
        with TestClient(app) as client:
            registered = client.post("/api/auth/register-business", json={
                "email": email,
                "password": "a sufficiently long test password",
                "business_name": "HTTP Test Shop",
            })
            assert registered.status_code == 201, registered.text
            owner_id = registered.json()["owner_id"]
            business_id = registered.json()["business_id"]
            login = client.post("/api/auth/login", json={
                "email": email, "password": "a sufficiently long test password",
            })
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            assert client.get("/api/auth/me", headers=headers).json()["owner_id"] == owner_id
            businesses = client.get("/api/businesses", headers=headers)
            assert businesses.status_code == 200
            assert {"business_id": business_id} in businesses.json()["businesses"]
            assert client.get(f"/api/businesses/{business_id}", headers=headers).status_code == 200
            assert client.post("/api/auth/logout", headers=headers).status_code == 200
            assert client.get("/api/auth/me", headers=headers).status_code == 401
    finally:
        app.dependency_overrides.clear()
        if owner_id:
            with Session(engine) as db:
                db.query(OwnerSession).filter_by(user_id=uuid.UUID(owner_id)).delete()
                db.query(BusinessMembership).filter_by(user_id=uuid.UUID(owner_id)).delete()
                db.query(OwnerAccount).filter_by(id=uuid.UUID(owner_id)).delete()
                db.query(Business).filter_by(id=uuid.UUID(business_id)).delete()
                db.commit()
        engine.dispose()
