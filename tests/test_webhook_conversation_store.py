import uuid
from unittest.mock import patch

from backend.app.webhook.conversation_store import record_incoming_message


def test_storage_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ASKDUKA_STORE_CONVERSATIONS", raising=False)
    with patch("backend.app.db.database.SessionLocal", create=True) as factory:
        record_incoming_message(uuid.uuid4(), "2348000000000", "hello")
        factory.assert_not_called()


def test_storage_disabled_even_with_empty_message(monkeypatch):
    monkeypatch.delenv("ASKDUKA_STORE_CONVERSATIONS", raising=False)
    record_incoming_message(uuid.uuid4(), "", "")
