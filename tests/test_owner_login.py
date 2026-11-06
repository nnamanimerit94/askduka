import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.app.owner_login import authenticate_owner
from backend.app.owner_security import hash_password


def test_login_verifies_active_owner_and_normalizes_email():
    owner_id = uuid.uuid4()
    owner = SimpleNamespace(id=owner_id, is_active=True, password_hash=hash_password("long secure password"))
    session = MagicMock()
    session.scalar.return_value = owner
    assert authenticate_owner(session, " OWNER@EXAMPLE.COM ", "long secure password") == owner_id
    assert authenticate_owner(session, "owner@example.com", "incorrect password") is None


def test_login_denies_missing_and_disabled_owner():
    session = MagicMock()
    session.scalar.return_value = None
    assert authenticate_owner(session, "missing@example.com", "long secure password") is None
    session.scalar.return_value = SimpleNamespace(id=uuid.uuid4(), is_active=False, password_hash=hash_password("long secure password"))
    assert authenticate_owner(session, "disabled@example.com", "long secure password") is None


def test_login_rejects_invalid_inputs():
    session = MagicMock()
    assert authenticate_owner(session, "", "pass") is None
    assert authenticate_owner(session, "owner@example.com", None) is None
    assert authenticate_owner(session, "owner@example.com", "a" * 1025) is None
    session.scalar.assert_not_called()
