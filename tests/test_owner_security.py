import uuid
from types import SimpleNamespace

import pytest

from backend.app.owner_security import hash_password, verify_password, has_business_access


def test_password_hash_is_salted_and_verifiable():
    password = "long secure passphrase 2026!"
    first = hash_password(password)
    second = hash_password(password)
    assert first != second
    assert password not in first
    assert verify_password(password, first)
    assert not verify_password("incorrect password", first)


def test_invalid_password_hash_is_rejected():
    assert not verify_password("anything", "not-a-valid-hash")
    assert not verify_password("anything", "scrypt$999999$8$1$aa$bb")
    with pytest.raises(ValueError):
        hash_password("short")


def test_business_access_requires_active_matching_owner():
    owner_id, other_id = uuid.uuid4(), uuid.uuid4()
    business_id, other_business = uuid.uuid4(), uuid.uuid4()
    membership = SimpleNamespace(user_id=owner_id, business_id=business_id, role="owner", is_active=True)
    assert has_business_access(owner_id, business_id, [membership])
    assert not has_business_access(other_id, business_id, [membership])
    assert not has_business_access(owner_id, other_business, [membership])
    assert not has_business_access(owner_id, business_id, [])
    assert not has_business_access(owner_id, business_id, [SimpleNamespace(user_id=owner_id, business_id=business_id, role="viewer", is_active=True)])
    assert not has_business_access(owner_id, business_id, [SimpleNamespace(user_id=owner_id, business_id=business_id, role="owner", is_active=False)])
