import uuid
from unittest.mock import patch
from backend.app.webhook import orchestrator


def test_storage_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ASKDUKA_STORE_CONVERSATIONS", raising=False)
    with patch("backend.app.webhook.conversation_store.SessionLocal", create=True) as factory:
        from backend.app.webhook.conversation_store import record_incoming_message
        record_incoming_message(uuid.uuid4(), "2348000000000", "hello")
        factory.assert_not_called()


def test_orchestrator_records_after_reply(monkeypatch):
    orchestrator._seen_message_ids.clear()
    business_id = uuid.uuid4()
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(business_id))
    monkeypatch.setattr(orchestrator, "retrieve", lambda *args: [])
    monkeypatch.setattr(orchestrator, "generate_answer", lambda *args: {"answer": "hello"})
    monkeypatch.setattr(orchestrator, "send_text_message", lambda *args: None)
    calls = []
    monkeypatch.setattr(orchestrator, "record_incoming_message", lambda *args: calls.append(args))
    orchestrator.handle_message({"id": "new-1", "type": "text", "from": "2348000000000", "text": {"body": "price?"}})
    assert calls == [(business_id, "2348000000000", "price?")]
