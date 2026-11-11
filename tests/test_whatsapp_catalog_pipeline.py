"""Verify the customer-message orchestration contract without external services."""
import importlib
import sys
import types
import uuid
from unittest.mock import MagicMock


def test_catalog_question_reaches_whatsapp_reply(monkeypatch):
    business_id = uuid.uuid4()
    retrieval = types.ModuleType("backend.app.retrieval")
    retrieval.retrieve = MagicMock(return_value=[{
        "chunk": types.SimpleNamespace(
            chunk_text="EliteBook 840 G8 costs NGN 250000",
            document=types.SimpleNamespace(filename="catalog.txt"),
        ),
        "similarity": 0.99,
    }])
    monkeypatch.setitem(sys.modules, "backend.app.retrieval", retrieval)
    import backend.app.webhook.orchestrator as orchestrator
    orchestrator = importlib.reload(orchestrator)
    sent = []
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(business_id))
    monkeypatch.setattr(orchestrator, "generate_answer", lambda question, chunks: {
        "answer": chunks[0]["chunk_text"],
        "sources": [chunks[0]["source_document"]],
    })
    monkeypatch.setattr(orchestrator, "send_text_message", lambda phone, answer: sent.append((phone, answer)))
    monkeypatch.setattr(orchestrator, "record_incoming_message", lambda *args: None)
    orchestrator._seen_message_ids.clear()
    message = {
        "id": "test-catalog-001",
        "type": "text",
        "from": "2348000000000",
        "text": {"body": "How much is the EliteBook 840 G8?"},
    }
    orchestrator.handle_message(message)
    retrieval.retrieve.assert_called_once_with(business_id, "How much is the EliteBook 840 G8?")
    assert sent == [("2348000000000", "EliteBook 840 G8 costs NGN 250000")]
    orchestrator.handle_message(message)
    assert len(sent) == 1
