"""Transactional owner session lifecycle; not yet mounted as public routes."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.db.owner_models import OwnerAccount
from backend.app.db.session_models import OwnerSession
from backend.app.owner_login import authenticate_owner
from backend.app.owner_sessions import (
    hash_session_token, issue_session_token, session_expiry, session_is_active,
)


def login_owner(session: Session, email: str, password: str) -> str | None:
    """Verify credentials and persist a hashed session. Return raw token once."""
    owner_id = authenticate_owner(session, email, password)
    if owner_id is None:
        return None
    token, token_hash = issue_session_token()
    session.add(OwnerSession(user_id=owner_id, token_hash=token_hash, expires_at=session_expiry()))
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return token


def current_owner_id(session: Session, token: str) -> uuid.UUID | None:
    """Resolve only active, unrevoked sessions belonging to active owners."""
    try:
        digest = hash_session_token(token)
    except (ValueError, UnicodeError):
        return None
    row = session.execute(
        select(OwnerSession, OwnerAccount)
        .join(OwnerAccount, OwnerAccount.id == OwnerSession.user_id)
        .where(OwnerSession.token_hash == digest)
    ).one_or_none()
    if row is None:
        return None
    owner_session, owner = row
    if owner.is_active is not True or not session_is_active(owner_session.expires_at, owner_session.revoked_at):
        return None
    return owner.id


def logout_owner(session: Session, token: str) -> bool:
    """Revoke a session; repeated or unknown tokens return False."""
    try:
        digest = hash_session_token(token)
    except (ValueError, UnicodeError):
        return False
    result = session.execute(
        update(OwnerSession)
        .where(OwnerSession.token_hash == digest, OwnerSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    session.commit()
    return result.rowcount > 0
