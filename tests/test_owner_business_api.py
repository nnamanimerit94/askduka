import uuid
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.owner_business_api import router, db_session


db = MagicMock()
app = FastAPI()
app.include_router(router)
app.dependency_overrides[db_session] = lambda: db
client = TestClient(app)


def test_business_endpoints_require_authentication():
    assert client.get("/api/businesses").status_code == 401
    assert client.get(f"/api/businesses/{uuid.uuid4()}").status_code == 401


def test_owner_sees_only_active_memberships():
    own_business = uuid.uuid4()
    membership = MagicMock(business_id=own_business)
    db.scalars.return_value.all.return_value = [membership]
    with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
        response = client.get("/api/businesses", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 200
    assert response.json() == {"businesses": [{"business_id": str(own_business)}]}


def test_nonmember_cannot_access_business():
    db.scalar.return_value = None
    with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
        response = client.get(f"/api/businesses/{uuid.uuid4()}", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 404


def test_active_member_can_access_business():
    business_id = uuid.uuid4()
    db.scalar.return_value = MagicMock()
    with patch("backend.app.owner_business_api.current_owner_id", return_value=uuid.uuid4()):
        response = client.get(f"/api/businesses/{business_id}", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 200
    assert response.json() == {"business_id": str(business_id)}
