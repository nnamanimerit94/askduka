import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.app.owner_session_service import current_owner_id, login_owner, logout_owner
from backend.app.owner_sessions import hash_session_token


def test_login_creates_hashed_session_and_returns_raw_token():
    db = MagicMock()
    owner_id = uuid.uuid4()
    with patch("backend.app.owner_session_service.authenticate_owner", return_value=owner_id):
        token = login_owner(db, "owner@example.com", "long secure password")
    saved = db.add.call_args.args[0]
    assert saved.user_id == owner_id
    assert saved.token_hash == hash_session_token(token)
    assert saved.token_hash != token
    db.commit.assert_called_once()


def test_bad_credentials_never_create_session():
    db = MagicMock()
    with patch("backend.app.owner_session_service.authenticate_owner", return_value=None):
        assert login_owner(db, "owner@example.com", "wrong") is None
    db.add.assert_not_called()


def test_active_session_resolves_owner_and_expired_or_disabled_denied():
    db = MagicMock()
    owner_id = uuid.uuid4()
    row = SimpleNamespace(expires_at=datetime.now(timezone.utc) + timedelta(hours=1), revoked_at=None)
    owner = SimpleNamespace(id=owner_id, is_active=True)
    db.execute.return_value.one_or_none.return_value = (row, owner)
    assert current_owner_id(db, "opaque-token") == owner_id
    owner.is_active = False
    assert current_owner_id(db, "opaque-token") is None
    owner.is_active = True
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert current_owner_id(db, "opaque-token") is None


def test_logout_revokes_token():
    db = MagicMock()
    db.execute.return_value.rowcount = 1
    assert logout_owner(db, "opaque-token")
    db.commit.assert_called_once()
    assert not logout_owner(db, "")
