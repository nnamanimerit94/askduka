import uuid
import sys
from unittest.mock import MagicMock, patch

from sqlalchemy.dialects import postgresql
from backend.app.webhook.conversation_store import record_incoming_message


def test_conversation_uses_atomic_conflict_update(monkeypatch):
    monkeypatch.setenv("ASKDUKA_STORE_CONVERSATIONS", "true")
    db = MagicMock()
    manager = MagicMock()
    manager.__enter__.return_value = db
    manager.__exit__.return_value = False
    fake_database = type(sys)("backend.app.db.database")
    fake_database.SessionLocal = lambda: manager
    with patch.dict(sys.modules, {"backend.app.db.database": fake_database}):
        record_incoming_message(uuid.uuid4(), "2348000000000", "hello")
    statement = db.execute.call_args.args[0]
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT ON CONSTRAINT uq_conversations_business_customer DO UPDATE" in compiled
    db.commit.assert_called_once()
