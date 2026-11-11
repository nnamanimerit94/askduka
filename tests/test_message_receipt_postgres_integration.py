"""PostgreSQL-backed atomic message receipt tests; isolated test database only."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.app.webhook.message_receipts import claim_message, mark_failed, mark_sent


@pytest.mark.skipif(not os.getenv("ASKDUKA_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL")
def test_receipt_claims_are_atomic_across_sessions():
    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    assert url.split("?")[0].endswith("/askduka_test"), "Refusing non-test database"
    engine = create_engine(url, pool_size=4, max_overflow=2)
    business_id = uuid.uuid4()
    message_id = f"wamid.concurrent.{uuid.uuid4()}"
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id UUID PRIMARY KEY, name TEXT NOT NULL
                )
            """))
            connection.execute(text("""
                INSERT INTO businesses (id, name) VALUES (:id, 'Receipt Test Business')
            """), {"id": business_id})
            sql = Path("database/migrations/006_whatsapp_message_receipts.sql").read_text()
            # Strip SQL comments before splitting statements (comments contain semicolons).
            executable = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
            for statement in executable.split(";"):
                if statement.strip():
                    connection.execute(text(statement))
        barrier = Barrier(2)
        def attempt_claim(_):
            barrier.wait(timeout=10)
            with Session(engine) as session:
                claimed = claim_message(session, business_id, message_id)
                session.commit()
                return claimed
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt_claim, range(2)))
        assert sorted(outcomes) == [False, True]
        with Session(engine) as session:
            assert mark_sent(session, business_id, message_id) is True
            session.commit()
        with Session(engine) as session:
            assert claim_message(session, business_id, message_id) is False
            assert mark_failed(session, business_id, message_id) is False
            session.commit()
        with engine.connect() as connection:
            receipt = connection.execute(text("""
                SELECT status, attempts FROM whatsapp_message_receipts
                WHERE business_id = :business_id AND message_id = :message_id
            """), {"business_id": business_id, "message_id": message_id}).one()
            assert receipt.status == "sent"
            assert receipt.attempts == 1
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM businesses WHERE id = :id"), {"id": business_id})
        engine.dispose()
