from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.owner_registration import RegistrationError, register_owner
from backend.app.owner_security import verify_password


def test_registration_normalizes_email_and_hashes_password():
    session = MagicMock()
    password = "very long private passphrase"
    owner = register_owner(session, "  OWNER@Example.com  ", password)
    assert owner.email == "owner@example.com"
    assert owner.password_hash != password
    assert verify_password(password, owner.password_hash)
    session.add.assert_called_once_with(owner)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(owner)


@pytest.mark.parametrize("email,password", [
    ("invalid", "long enough password"),
    ("", "long enough password"),
    ("owner@example.com", "short"),
])
def test_invalid_registration_does_not_write(email, password):
    session = MagicMock()
    with pytest.raises(RegistrationError):
        register_owner(session, email, password)
    session.add.assert_not_called()


def test_duplicate_email_rolls_back_without_leaking_details():
    session = MagicMock()
    session.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    with pytest.raises(RegistrationError, match="Account could not be registered"):
        register_owner(session, "owner@example.com", "long secure password")
    session.rollback.assert_called_once()
