"""Isolated webhook orchestration tests for opt-in durable receipts."""
import sys
import types
import uuid

import pytest

import importlib


@pytest.fixture
def orchestrator(monkeypatch):
    retrieval = types.ModuleType("backend.app.retrieval")
    retrieval.retrieve = lambda *args: []
    monkeypatch.setitem(sys.modules, "backend.app.retrieval", retrieval)
    from backend.app.webhook import orchestrator as module
    return importlib.reload(module)


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def commit(self):
        pass


def test_durable_claim_skips_duplicate_and_records_success(monkeypatch, orchestrator):
    business_id = uuid.uuid4()
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(business_id))
    monkeypatch.setenv("ASKDUKA_USE_DURABLE_RECEIPTS", "true")
    database = types.ModuleType("backend.app.db.database")
    database.SessionLocal = FakeSession
    receipts = types.ModuleType("backend.app.webhook.message_receipts")
    claims = iter([True, False])
    receipts.claim_message = lambda *args: next(claims)
    receipts.receipt_status = lambda *args: "sent"
    marked = []
    receipts.mark_sent = lambda *args: marked.append("sent") or True
    receipts.mark_failed = lambda *args: marked.append("failed") or True
    monkeypatch.setitem(sys.modules, "backend.app.db.database", database)
    monkeypatch.setitem(sys.modules, "backend.app.webhook.message_receipts", receipts)
    sent = []
    monkeypatch.setattr(orchestrator, "_process_and_send", lambda *args: sent.append(args))
    monkeypatch.setattr(orchestrator, "record_incoming_message", lambda *args: None)
    message = {"id": "wamid.duplicate", "type": "text", "from": "234800000", "text": {"body": "Price?"}}
    orchestrator.handle_message(message)
    orchestrator.handle_message(message)
    assert len(sent) == 1
    assert marked == ["sent"]


def test_durable_failure_marks_failed_and_propagates(monkeypatch, orchestrator):
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(uuid.uuid4()))
    monkeypatch.setenv("ASKDUKA_USE_DURABLE_RECEIPTS", "true")
    database = types.ModuleType("backend.app.db.database")
    database.SessionLocal = FakeSession
    receipts = types.ModuleType("backend.app.webhook.message_receipts")
    receipts.claim_message = lambda *args: True
    marked = []
    receipts.mark_failed = lambda *args: marked.append("failed") or True
    receipts.mark_sent = lambda *args: marked.append("sent") or True
    receipts.receipt_status = lambda *args: "failed"
    monkeypatch.setitem(sys.modules, "backend.app.db.database", database)
    monkeypatch.setitem(sys.modules, "backend.app.webhook.message_receipts", receipts)
    def fail(*args):
        raise RuntimeError("send failed")
    monkeypatch.setattr(orchestrator, "_process_and_send", fail)
    message = {"id": "wamid.fail", "type": "text", "from": "234800000", "text": {"body": "Price?"}}
    with pytest.raises(RuntimeError, match="send failed"):
        orchestrator.handle_message(message)
    assert marked == ["failed"]


def test_durable_mode_fails_closed_without_db(monkeypatch, orchestrator):
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(uuid.uuid4()))
    monkeypatch.setenv("ASKDUKA_USE_DURABLE_RECEIPTS", "true")
    database = types.ModuleType("backend.app.db.database")
    def broken_session():
        raise RuntimeError("database unavailable")
    database.SessionLocal = broken_session
    monkeypatch.setitem(sys.modules, "backend.app.db.database", database)
    message = {"id": "wamid.db-down", "type": "text", "from": "234800000", "text": {"body": "Price?"}}
    with pytest.raises(RuntimeError, match="database unavailable"):
        orchestrator.handle_message(message)


def test_inflight_duplicate_is_not_acknowledged(monkeypatch, orchestrator):
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(uuid.uuid4()))
    monkeypatch.setenv("ASKDUKA_USE_DURABLE_RECEIPTS", "true")
    database = types.ModuleType("backend.app.db.database")
    database.SessionLocal = FakeSession
    receipts = types.ModuleType("backend.app.webhook.message_receipts")
    receipts.claim_message = lambda *args: False
    receipts.receipt_status = lambda *args: "processing"
    receipts.mark_failed = lambda *args: True
    receipts.mark_sent = lambda *args: True
    monkeypatch.setitem(sys.modules, "backend.app.db.database", database)
    monkeypatch.setitem(sys.modules, "backend.app.webhook.message_receipts", receipts)
    message = {"id": "wamid.processing", "type": "text", "from": "234800000", "text": {"body": "Price?"}}
    with pytest.raises(RuntimeError, match="not complete: processing"):
        orchestrator.handle_message(message)


@pytest.mark.parametrize("business_id", [None, "not-a-uuid"])
def test_durable_mode_rejects_missing_or_invalid_business_id(monkeypatch, orchestrator, business_id):
    monkeypatch.setenv("ASKDUKA_USE_DURABLE_RECEIPTS", "true")
    if business_id is None:
        monkeypatch.delenv("ASKDUKA_BUSINESS_ID", raising=False)
    else:
        monkeypatch.setenv("ASKDUKA_BUSINESS_ID", business_id)
    message = {"id": "wamid.misconfigured", "type": "text", "from": "234800000", "text": {"body": "Price?"}}
    with pytest.raises(RuntimeError, match="requires a valid ASKDUKA_BUSINESS_ID"):
        orchestrator.handle_message(message)
