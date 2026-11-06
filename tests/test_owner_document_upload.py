import uuid
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.owner_auth_api import db_session
from backend.app.owner_documents_api import router


db = MagicMock()
app = FastAPI()
app.include_router(router)
app.dependency_overrides[db_session] = lambda: db
client = TestClient(app)


def post_document(filename, data, authorized=True):
    db.scalar.return_value = MagicMock() if authorized else None
    with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
        return client.post(
            f"/api/businesses/{uuid.uuid4()}/documents",
            headers={"Authorization": "Bearer valid"},
            files={"file": (filename, data, "text/plain")},
        )


def test_upload_requires_authentication():
    response = client.post(
        f"/api/businesses/{uuid.uuid4()}/documents",
        files={"file": ("catalog.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 401


def test_upload_denies_nonmembers():
    assert post_document("catalog.txt", b"hello", authorized=False).status_code == 404


def test_upload_rejects_unsupported_and_oversized_files():
    assert post_document("catalog.pdf", b"fake pdf").status_code == 422
    assert post_document("catalog.txt", b"x" * (256 * 1024 + 1)).status_code == 413
    assert post_document("catalog.txt", b"").status_code == 422
    assert post_document("catalog.txt", bytes([255])).status_code == 422


def test_upload_persists_text_chunks_for_authorized_business():
    db.reset_mock()
    response = post_document("catalog.txt", b"AskDuka catalog")
    assert response.status_code == 201
    assert response.json()["status"] == "ready"
    assert db.flush.called
    assert db.commit.called
    assert db.add.call_count >= 2
