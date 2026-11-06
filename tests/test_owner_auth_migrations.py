"""Verify additive owner migrations against an isolated PostgreSQL database.

Initial schema requires pgvector; this test simulates an existing businesses
table, then applies the owner-specific migrations in order.
"""
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text


MIGRATIONS = Path(__file__).resolve().parents[1] / "database" / "migrations"


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL")
def test_owner_migrations_apply_twice_and_preserve_existing_business():
    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    assert url.split("?")[0].endswith("/askduka_test")
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """))
            connection.execute(text("""
                INSERT INTO businesses (id, name)
                VALUES ('b4ccbf2e-6b39-44ad-87b6-63e97ebd7ed1', 'Existing business')
                ON CONFLICT (id) DO NOTHING
            """))
            for _ in range(2):
                for filename in ("002_owner_identity.sql", "003_owner_sessions.sql"):
                    connection.exec_driver_sql((MIGRATIONS / filename).read_text(encoding="utf-8"))
            assert connection.scalar(text("""
                SELECT name FROM businesses
                WHERE id = 'b4ccbf2e-6b39-44ad-87b6-63e97ebd7ed1'
            """)) == "Existing business"
        names = set(inspect(engine).get_table_names())
        assert {"businesses", "owner_accounts", "business_memberships", "owner_sessions"} <= names
    finally:
        engine.dispose()
