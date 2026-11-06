"""Isolated PostgreSQL integration test for signup -> login -> business access."""
import os
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.db.models import Base, Business
from backend.app.db.owner_models import BusinessMembership, OwnerAccount
from backend.app.db.session_models import OwnerSession
from backend.app.owner_onboarding import onboard_new_business
from backend.app.owner_session_service import current_owner_id, login_owner, logout_owner


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL")
def test_new_owner_can_login_and_access_only_their_business():
    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    assert url.split("?")[0].endswith("/askduka_test"), "Use dedicated test database"
    engine = create_engine(url)
    owner_id = None
    business_id = None
    try:
        Base.metadata.create_all(engine, tables=[
            Business.__table__, OwnerAccount.__table__,
            BusinessMembership.__table__, OwnerSession.__table__,
        ])
        email = f"onboard-{uuid.uuid4()}@example.com"
        with Session(engine) as db:
            owner_id, business_id = onboard_new_business(
                db, email, "a long unique test password", "New Test Business"
            )
            assert db.scalar(select(Business.name).where(Business.id == business_id)) == "New Test Business"
            assert login_owner(db, email, "incorrect password") is None
            token = login_owner(db, email, "a long unique test password")
            assert token is not None
            assert current_owner_id(db, token) == owner_id
            memberships = db.scalars(select(BusinessMembership).where(
                BusinessMembership.user_id == owner_id,
                BusinessMembership.is_active.is_(True),
            )).all()
            assert len(memberships) == 1
            assert memberships[0].business_id == business_id
            assert memberships[0].role == "owner"
            assert logout_owner(db, token)
            assert current_owner_id(db, token) is None
    finally:
        if owner_id is not None:
            with Session(engine) as db:
                db.query(OwnerSession).filter_by(user_id=owner_id).delete()
                db.query(BusinessMembership).filter_by(user_id=owner_id).delete()
                db.query(OwnerAccount).filter_by(id=owner_id).delete()
                db.query(Business).filter_by(id=business_id).delete()
                db.commit()
        engine.dispose()
