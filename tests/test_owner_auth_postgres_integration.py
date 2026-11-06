"""Owner authentication persistence test using isolated PostgreSQL."""
import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.models import Base, Business
from backend.app.db.owner_models import OwnerAccount, BusinessMembership
from backend.app.db.session_models import OwnerSession
from backend.app.owner_registration import register_owner
from backend.app.owner_session_service import login_owner, current_owner_id, logout_owner


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL")
def test_owner_auth_lifecycle_with_postgres():
    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    assert url.split("?")[0].endswith("/askduka_test"), "Use dedicated askduka_test database"
    engine = create_engine(url)
    owner_id = None
    try:
        Base.metadata.create_all(engine, tables=[
            Business.__table__, OwnerAccount.__table__,
            BusinessMembership.__table__, OwnerSession.__table__,
        ])
        email = f"test-{uuid.uuid4()}@example.com"
        with Session(engine) as db:
            owner = register_owner(db, email, "a sufficiently long test password")
            owner_id = owner.id
            assert login_owner(db, email, "wrong password") is None
            token = login_owner(db, email, "a sufficiently long test password")
            assert token
            assert current_owner_id(db, token) == owner_id
            assert logout_owner(db, token)
            assert current_owner_id(db, token) is None
            assert not logout_owner(db, token)
    finally:
        if owner_id is not None:
            with Session(engine) as db:
                db.query(OwnerSession).filter_by(user_id=owner_id).delete()
                db.query(OwnerAccount).filter_by(id=owner_id).delete()
                db.commit()
        engine.dispose()
