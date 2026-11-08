"""Real PostgreSQL HTTP upload and cross-business isolation test.

Uses a disposable pgvector-enabled askduka_test database.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.models import Base, Business, Document, DocumentChunk
from backend.app.db.owner_models import BusinessMembership, OwnerAccount
from backend.app.db.session_models import OwnerSession
from backend.app.owner_app import app
from backend.app.owner_auth_api import db_session


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL")
def test_owner_document_http_upload_is_scoped(monkeypatch):
    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    assert url.split("?")[0].endswith("/askduka_test"), "Refusing non-test database"
    engine = create_engine(url)
    owners = []
    businesses = []
    def override_db():
        with Session(engine) as db:
            yield db
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        Base.metadata.create_all(engine, tables=[
            Business.__table__, OwnerAccount.__table__, BusinessMembership.__table__,
            OwnerSession.__table__, Document.__table__, DocumentChunk.__table__,
        ])
        app.dependency_overrides[db_session] = override_db
        monkeypatch.setenv("ASKDUKA_ENABLE_OWNER_SIGNUP", "true")
        with TestClient(app) as client:
            tokens = []
            for index in (1, 2):
                email = f"doc-http-{uuid.uuid4()}@example.com"
                registration = client.post("/api/auth/register-business", json={
                    "email": email, "password": "a sufficiently long test password",
                    "business_name": f"Isolated Business {index}",
                })
                assert registration.status_code == 201, registration.text
                owners.append(uuid.UUID(registration.json()["owner_id"]))
                businesses.append(uuid.UUID(registration.json()["business_id"]))
                login = client.post("/api/auth/login", json={
                    "email": email, "password": "a sufficiently long test password",
                })
                assert login.status_code == 200, login.text
                tokens.append(login.json()["access_token"])
            first_headers = {"Authorization": f"Bearer {tokens[0]}"}
            second_headers = {"Authorization": f"Bearer {tokens[1]}"}
            path = f"/api/businesses/{businesses[0]}/documents"
            assert client.get(path, headers=second_headers).status_code == 404
            assert client.post(path, headers=second_headers, files={
                "file": ("stolen.txt", b"not allowed", "text/plain"),
            }).status_code == 404
            upload = client.post(path, headers=first_headers, files={
                "file": ("catalog.txt", b"Private business catalog", "text/plain"),
            })
            assert upload.status_code == 201, upload.text
            listed = client.get(path, headers=first_headers)
            assert listed.status_code == 200
            assert any(doc["document_id"] == upload.json()["document_id"] for doc in listed.json()["documents"])
            assert client.get(path, headers=second_headers).status_code == 404
    finally:
        app.dependency_overrides.clear()
        if owners:
            with Session(engine) as db:
                for business in businesses:
                    docs = db.query(Document).filter_by(business_id=business).all()
                    for doc in docs:
                        db.query(DocumentChunk).filter_by(document_id=doc.id).delete()
                        db.delete(doc)
                db.flush()
                for owner in owners:
                    db.query(OwnerSession).filter_by(user_id=owner).delete()
                    db.query(BusinessMembership).filter_by(user_id=owner).delete()
                    db.query(OwnerAccount).filter_by(id=owner).delete()
                for business in businesses:
                    db.query(Business).filter_by(id=business).delete()
                db.commit()
        engine.dispose()
