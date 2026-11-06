import uuid
from types import SimpleNamespace
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


def test_document_list_requires_authentication():
    assert client.get(f"/api/businesses/{uuid.uuid4()}/documents").status_code == 401


def test_nonmember_cannot_list_documents():
    db.scalar.return_value = None
    with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
        response = client.get(
            f"/api/businesses/{uuid.uuid4()}/documents",
            headers={"Authorization": "Bearer valid"},
        )
    assert response.status_code == 404


def test_member_lists_only_business_documents():
    business_id = uuid.uuid4()
    document_id = uuid.uuid4()
    db.scalar.return_value = MagicMock()
    db.scalars.return_value.all.return_value = [
        SimpleNamespace(id=document_id, filename="catalog.pdf", file_type="pdf", status="ready")
    ]
    with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
        response = client.get(
            f"/api/businesses/{business_id}/documents",
            headers={"Authorization": "Bearer valid"},
        )
    assert response.status_code == 200
    assert response.json() == {"documents": [
        {"document_id": str(document_id), "filename": "catalog.pdf", "file_type": "pdf", "status": "ready"}
    ]}
    query = db.scalars.call_args.args[0]
    assert business_id in query.compile().params.values()
