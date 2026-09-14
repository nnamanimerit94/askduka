import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.generation import FALLBACK_ANSWER
from backend.app.main import create_app
from backend.app.webhook import orchestrator


class FakeDocument:
    def __init__(self, filename):
        self.filename = filename


class FakeChunk:
    def __init__(self, text, filename):
        self.chunk_text = text
        self.document = FakeDocument(filename)


def message_payload(
    text="How much is jollof rice?",
    message_id="wamid.1",
    message_type="text",
):
    message = {
        "from": "2348012345678",
        "id": message_id,
        "timestamp": "1700000000",
        "type": message_type,
    }

    if message_type == "text":
        message["text"] = {"body": text}

    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "phone_number_id": "999888"
                            },
                            "contacts": [
                                {
                                    "wa_id": "2348012345678",
                                    "profile": {"name": "Ada"},
                                }
                            ],
                            "messages": [message],
                        },
                    }
                ],
            }
        ],
    }


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def reset_seen_messages():
    orchestrator._seen_message_ids.clear()

    yield

    orchestrator._seen_message_ids.clear()


@pytest.fixture()
def whatsapp_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify-token")
    monkeypatch.setenv("ASKDUKA_BUSINESS_ID", str(uuid.uuid4()))


@pytest.fixture()
def stub_pipeline(monkeypatch):
    """Replace retrieval, generation and sending with fakes."""

    sent = []
    generated_with = []

    def fake_retrieve(business_id, query, limit=5):
        return [
            {
                "chunk": FakeChunk(
                    "Jollof Rice - ₦2,500",
                    "catalog.txt",
                ),
                "similarity": 0.92,
            }
        ]

    def fake_generate_answer(customer_message, chunks):
        generated_with.append(
            {
                "customer_message": customer_message,
                "chunks": chunks,
            }
        )

        return {
            "answer": "Jollof Rice costs ₦2,500.",
            "sources": ["catalog.txt"],
            "confidence": "grounded",
        }

    def fake_send_text_message(to, body):
        sent.append({"to": to, "body": body})

    monkeypatch.setattr(orchestrator, "retrieve", fake_retrieve)
    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        fake_generate_answer,
    )
    monkeypatch.setattr(
        orchestrator,
        "send_text_message",
        fake_send_text_message,
    )

    return {"sent": sent, "generated_with": generated_with}


def test_verify_webhook_success(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify-token")

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_verify_webhook_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify-token")

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403


def test_text_message_receives_grounded_reply(
    client,
    whatsapp_env,
    stub_pipeline,
):
    response = client.post("/webhook", json=message_payload())

    assert response.status_code == 200

    assert len(stub_pipeline["sent"]) == 1
    assert stub_pipeline["sent"][0] == {
        "to": "2348012345678",
        "body": "Jollof Rice costs ₦2,500.",
    }

    generated = stub_pipeline["generated_with"][0]

    assert generated["customer_message"] == "How much is jollof rice?"

    assert generated["chunks"] == [
        {
            "chunk_text": "Jollof Rice - ₦2,500",
            "similarity": 0.92,
            "source_document": "catalog.txt",
        }
    ]


def test_no_relevant_chunks_gets_fallback_answer(
    client,
    whatsapp_env,
    monkeypatch,
):
    monkeypatch.setattr(
        orchestrator,
        "retrieve",
        lambda business_id, query, limit=5: [],
    )

    sent = []

    monkeypatch.setattr(
        orchestrator,
        "send_text_message",
        lambda to, body: sent.append({"to": to, "body": body}),
    )

    response = client.post("/webhook", json=message_payload())

    assert response.status_code == 200

    assert sent == [
        {
            "to": "2348012345678",
            "body": FALLBACK_ANSWER,
        }
    ]


def test_duplicate_message_is_answered_once(
    client,
    whatsapp_env,
    stub_pipeline,
):
    payload = message_payload(message_id="wamid.duplicate")

    client.post("/webhook", json=payload)
    client.post("/webhook", json=payload)

    assert len(stub_pipeline["sent"]) == 1


def test_status_update_is_acknowledged_without_reply(
    client,
    stub_pipeline,
):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.1",
                                    "status": "delivered",
                                }
                            ]
                        },
                    }
                ],
            }
        ],
    }

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert stub_pipeline["sent"] == []


def test_non_text_message_is_ignored(
    client,
    whatsapp_env,
    stub_pipeline,
):
    payload = message_payload(message_type="image")

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert stub_pipeline["sent"] == []


def test_processing_failure_still_acknowledges(
    client,
    whatsapp_env,
    monkeypatch,
):
    monkeypatch.setattr(
        orchestrator,
        "retrieve",
        lambda business_id, query, limit=5: [],
    )

    def failing_send(to, body):
        raise RuntimeError("WhatsApp API is down")

    monkeypatch.setattr(
        orchestrator,
        "send_text_message",
        failing_send,
    )

    response = client.post("/webhook", json=message_payload())

    assert response.status_code == 200
