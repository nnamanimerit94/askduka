import uuid
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.owner_auth_api import db_session, router
from backend.app.owner_onboarding import onboard_new_business
from backend.app.db.models import Business
from backend.app.db.owner_models import BusinessMembership, OwnerAccount


db = MagicMock()
app = FastAPI()
app.include_router(router)
app.dependency_overrides[db_session] = lambda: db
client = TestClient(app)


def test_onboarding_creates_new_owner_business_membership_atomically():
    session = MagicMock()
    owner_id, business_id = onboard_new_business(
        session, "  OWNER@EXAMPLE.COM ", "secure password 1234", " My Shop "
    )
    added = [call.args[0] for call in session.add.call_args_list]
    owner = next(item for item in added if isinstance(item, OwnerAccount))
    business = next(item for item in added if isinstance(item, Business))
    membership = next(item for item in added if isinstance(item, BusinessMembership))
    assert owner.email == "owner@example.com"
    assert business.name == "My Shop"
    assert owner.id == owner_id and business.id == business_id
    assert membership.user_id == owner_id and membership.business_id == business_id
    session.commit.assert_called_once()


def test_onboarding_rejects_invalid_business_without_writing():
    session = MagicMock()
    from backend.app.owner_registration import RegistrationError
    try:
        onboard_new_business(session, "owner@example.com", "secure password 1234", " ")
        assert False, "Expected validation error"
    except RegistrationError:
        session.add.assert_not_called()


def test_registration_route_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ASKDUKA_ENABLE_OWNER_SIGNUP", raising=False)
    response = client.post("/api/auth/register-business", json={
        "email": "owner@example.com",
        "password": "secure password 1234",
        "business_name": "My Shop",
    })
    assert response.status_code == 404


def test_registration_route_calls_atomic_service_when_enabled(monkeypatch):
    monkeypatch.setenv("ASKDUKA_ENABLE_OWNER_SIGNUP", "true")
    with patch("backend.app.owner_auth_api.onboard_new_business", return_value=(uuid.uuid4(), uuid.uuid4())) as onboard:
        response = client.post("/api/auth/register-business", json={
            "email": "owner@example.com",
            "password": "secure password 1234",
            "business_name": "My Shop",
        })
    assert response.status_code == 201
    onboard.assert_called_once()
