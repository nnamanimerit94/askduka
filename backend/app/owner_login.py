"""Credential verification service; does not issue sessions or tokens."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.owner_models import OwnerAccount
from backend.app.owner_security import hash_password, verify_password

# An encoded dummy hash avoids a trivial timing difference between unknown
# accounts and wrong passwords. Rate limiting is still required at the API edge.
_DUMMY_HASH = hash_password("dummy-password-for-timing-only")


def authenticate_owner(session: Session, email: str, password: str) -> uuid.UUID | None:
    """Return active owner ID on valid credentials, otherwise None."""
    if not isinstance(email, str) or not isinstance(password, str):
        return None
    normalized = email.strip().lower()
    if not normalized or len(normalized) > 254 or len(password) > 1024:
        return None

    owner = session.scalar(select(OwnerAccount).where(OwnerAccount.email == normalized))
    stored_hash = owner.password_hash if owner is not None else _DUMMY_HASH
    verified = verify_password(password, stored_hash)
    if not verified or owner is None or owner.is_active is not True:
        return None
    return owner.id
