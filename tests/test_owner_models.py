from backend.app.db.models import Base, Business
from backend.app.db.owner_models import OwnerAccount, BusinessMembership


def test_owner_identity_tables_registered():
    assert "owner_accounts" in Base.metadata.tables
    assert "business_memberships" in Base.metadata.tables
    assert "businesses" in Base.metadata.tables


def test_membership_foreign_keys_reference_accounts_and_businesses():
    membership = Base.metadata.tables["business_memberships"]
    targets = {fk.target_fullname for fk in membership.foreign_keys}
    assert targets == {"owner_accounts.id", "businesses.id"}


def test_owner_email_and_membership_unique_constraints():
    accounts = Base.metadata.tables["owner_accounts"]
    assert accounts.c.email.unique
    membership = Base.metadata.tables["business_memberships"]
    assert any(
        getattr(constraint, "name", None) == "uq_business_membership"
        for constraint in membership.constraints
    )
