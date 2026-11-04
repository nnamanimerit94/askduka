import httpx
from backend.app import generation


def test_missing_context_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert generation.generate_answer("price?", [])["confidence"] == "fallback"


def test_missing_key_falls_back(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = generation.generate_answer("price?", [{"chunk_text": "Wig costs 50", "source_document": "catalog"}])
    assert result["confidence"] == "fallback"


def test_grounded_answer_uses_provider(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = {}

    def fake_post(self, url, **kwargs):
        captured["payload"] = kwargs["json"]
        return httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "The wig costs ₦50,000."}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    result = generation.generate_answer(
        "How much is the wig?",
        [{"chunk_text": "The wig costs ₦50,000.", "source_document": "catalog.txt"}],
    )
    assert result["answer"] == "The wig costs ₦50,000."
    assert result["sources"] == ["catalog.txt"]
    assert "The wig costs ₦50,000." in captured["payload"]["messages"][0]["content"]


def test_provider_error_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def broken_post(self, url, **kwargs):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx.Client, "post", broken_post)
    result = generation.generate_answer(
        "Price?", [{"chunk_text": "Price 100", "source_document": "catalog"}]
    )
    assert result["confidence"] == "fallback"
