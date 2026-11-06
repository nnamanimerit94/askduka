"""Opaque owner session token primitives.

Only SHA-256 token digests are stored. Tokens are returned once at creation.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone


SESSION_LIFETIME = timedelta(hours=12)


def issue_session_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hash_session_token(token)


def hash_session_token(token: str) -> str:
    if not isinstance(token, str) or not token or len(token) > 256:
        raise ValueError("Invalid session token")
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def session_is_active(expires_at: datetime, revoked_at: datetime | None = None, *, now: datetime | None = None) -> bool:
    if expires_at.tzinfo is None:
        return False
    now = now or datetime.now(timezone.utc)
    return revoked_at is None and now < expires_at


def session_expiry(*, now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)) + SESSION_LIFETIME
