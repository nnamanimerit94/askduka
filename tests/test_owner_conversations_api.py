import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.app.owner_app import app
from backend.app.owner_auth_api import db_session


def test_conversations_requires_authentication():
    response = TestClient(app).get(f"/api/businesses/{uuid.uuid4()}/conversations")
    assert response.status_code == 401


def test_conversations_rejects_other_business():
    db = MagicMock()
    db.scalar.return_value = None
    app.dependency_overrides[db_session] = lambda: db
    try:
        with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
            response = TestClient(app).get(
                f"/api/businesses/{uuid.uuid4()}/conversations",
                headers={"Authorization": "Bearer valid"},
            )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
