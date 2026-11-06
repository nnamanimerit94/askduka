"""Atomic creation of a new owner and a new business; never claim existing businesses."""
import re
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import Business
from backend.app.db.owner_models import BusinessMembership, OwnerAccount
from backend.app.owner_registration import RegistrationError
from backend.app.owner_security import hash_password


_EMAIL = re.compile(r"^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")


def onboard_new_business(session: Session, email: str, password: str, business_name: str):
    normalized = email.strip().lower()
    name = business_name.strip()
    if len(normalized) > 254 or not _EMAIL.fullmatch(normalized):
        raise RegistrationError("Invalid email address")
    if not 12 <= len(password) <= 1024:
        raise RegistrationError("Password must be 12 to 1024 characters")
    if not 2 <= len(name) <= 120:
        raise RegistrationError("Business name must be 2 to 120 characters")
    owner = OwnerAccount(id=uuid.uuid4(), email=normalized, password_hash=hash_password(password))
    business = Business(id=uuid.uuid4(), name=name)
    membership = BusinessMembership(
        id=uuid.uuid4(), user_id=owner.id, business_id=business.id, role="owner", is_active=True
    )
    try:
        session.add(owner)
        session.add(business)
        session.add(membership)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise RegistrationError("Account could not be registered") from exc
    except Exception:
        session.rollback()
        raise
    return owner.id, business.id
