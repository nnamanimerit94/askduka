import uuid

import pytest

from backend.app.webhook.message_receipts import claim_message, mark_failed, mark_sent


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((str(statement), params))
        return FakeResult(self.result)


def test_new_message_claim_is_atomic_insert():
    business_id = uuid.uuid4()
    session = FakeSession("wamid.1")
    assert claim_message(session, business_id, "wamid.1") is True
    sql, params = session.calls[0]
    assert "ON CONFLICT (business_id, message_id) DO UPDATE" in sql
    assert "WHERE whatsapp_message_receipts.status = 'failed'" in sql
    assert "attempts = whatsapp_message_receipts.attempts + 1" in sql
    assert "RETURNING message_id" in sql
    assert params == {"business_id": business_id, "message_id": "wamid.1"}


def test_existing_receipt_is_not_claimed_again():
    assert claim_message(FakeSession(None), uuid.uuid4(), "wamid.1") is False


@pytest.mark.parametrize("message_id", ["", "  ", None])
def test_claim_rejects_missing_provider_id(message_id):
    with pytest.raises(ValueError):
        claim_message(FakeSession(None), uuid.uuid4(), message_id)


@pytest.mark.parametrize("transition", [mark_sent, mark_failed])
def test_receipt_transition_requires_processing_state(transition):
    session = FakeSession("wamid.1")
    assert transition(session, uuid.uuid4(), "wamid.1") is True
    sql, _ = session.calls[0]
    assert "status = 'processing'" in sql
    assert "RETURNING message_id" in sql
    assert transition(FakeSession(None), uuid.uuid4(), "wamid.1") is False
