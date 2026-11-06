from datetime import datetime, timedelta, timezone

import pytest

from backend.app.db.models import Base
from backend.app.db.session_models import OwnerSession
from backend.app.owner_sessions import (
    hash_session_token, issue_session_token, session_expiry, session_is_active,
)


def test_session_token_is_random_and_only_hash_is_persisted():
    token, digest = issue_session_token()
    token2, digest2 = issue_session_token()
    assert token != token2
    assert digest != digest2
    assert digest == hash_session_token(token)
    assert len(digest) == 64
    assert token not in digest


def test_session_expiration_and_revocation():
    now = datetime.now(timezone.utc)
    assert session_is_active(now + timedelta(minutes=1), now=now)
    assert not session_is_active(now, now=now)
    assert not session_is_active(now + timedelta(minutes=1), revoked_at=now, now=now)
    assert not session_is_active(datetime.utcnow(), now=now)
    assert session_expiry(now=now) == now + timedelta(hours=12)


def test_session_model_has_user_foreign_key_and_unique_hash():
    table = Base.metadata.tables["owner_sessions"]
    assert "owner_accounts.id" in {fk.target_fullname for fk in table.foreign_keys}
    assert table.c.token_hash.unique


@pytest.mark.parametrize("token", ["", "x" * 257, None])
def test_invalid_session_tokens_rejected(token):
    with pytest.raises(ValueError):
        hash_session_token(token)
