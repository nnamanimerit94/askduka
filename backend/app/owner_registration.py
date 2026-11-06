"""Transactional owner registration service; not exposed as a public endpoint."""
import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.owner_models import OwnerAccount
from backend.app.owner_security import hash_password

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegistrationError(ValueError):
    pass


def register_owner(session: Session, email: str, password: str) -> OwnerAccount:
    """Create an owner with a salted password hash.

    Does not create business memberships; ownership must be established by
    a separately authorized workflow. Caller must use a dedicated session.
    """
    if not isinstance(email, str):
        raise RegistrationError("Invalid email address")
    normalized = email.strip().lower()
    if len(normalized) > 254 or not _EMAIL.fullmatch(normalized):
        raise RegistrationError("Invalid email address")
    if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
        raise RegistrationError("Password must be 12 to 1024 characters")

    owner = OwnerAccount(email=normalized, password_hash=hash_password(password))
    session.add(owner)
    try:
        session.commit()
        session.refresh(owner)
    except IntegrityError as exc:
        session.rollback()
        raise RegistrationError("Account could not be registered") from exc
    return owner
