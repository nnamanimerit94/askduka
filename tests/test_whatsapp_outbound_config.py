import pytest
import httpx
from backend.app.webhook.whatsapp_client import send_text_message


@pytest.mark.parametrize("missing", ["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"])
def test_missing_credentials_fail_without_http(monkeypatch, missing):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    monkeypatch.delenv(missing)
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: pytest.fail("HTTP must not be called"))
    with pytest.raises(ValueError):
        send_text_message("2348000000000", "Hello")


@pytest.mark.parametrize("phone,body", [("", "Hello"), ("2348000000000", "")])
def test_empty_recipient_or_message_fails_without_http(monkeypatch, phone, body):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: pytest.fail("HTTP must not be called"))
    with pytest.raises(ValueError):
        send_text_message(phone, body)


def test_configured_whatsapp_send_uses_expected_payload(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    captured = {}
    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(200, json={"messages": [{"id": "wamid.test"}]}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", fake_post)
    result = send_text_message("2348000000000", "Hello")
    assert result["messages"][0]["id"] == "wamid.test"
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["json"]["to"] == "2348000000000"
    assert captured["json"]["text"]["body"] == "Hello"
