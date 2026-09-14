import pytest
import numpy as np

from backend.app.ingestion import embeddings


def test_embed_documents_empty_input():
    result = embeddings.embed_documents([])

    assert result == []


def test_embed_documents_success(monkeypatch):
    class FakeModel:
        def encode_document(self, texts, convert_to_numpy):
            assert texts == [
                "Jollof Rice - ₦2,500",
                "Fried Rice - ₦3,000",
            ]
            assert convert_to_numpy is True

            return np.array([
                [0.1] * embeddings.EMBEDDING_DIMENSION,
                [0.2] * embeddings.EMBEDDING_DIMENSION,
            ])

    monkeypatch.setattr(
        embeddings,
        "_model",
        FakeModel(),
    )

    result = embeddings.embed_documents(
        [
            "Jollof Rice - ₦2,500",
            "Fried Rice - ₦3,000",
        ]
    )

    assert len(result) == 2
    assert len(result[0]) == 384
    assert len(result[1]) == 384


def test_embed_documents_uses_document_encoder(monkeypatch):
    calls = []

    class FakeModel:
        def encode_document(self, texts, convert_to_numpy):
            calls.append(
                {
                    "texts": texts,
                    "convert_to_numpy": convert_to_numpy,
                }
            )

            return np.array([
                [0.5] * embeddings.EMBEDDING_DIMENSION,
                [0.6] * embeddings.EMBEDDING_DIMENSION,
            ])

    monkeypatch.setattr(
        embeddings,
        "_model",
        FakeModel(),
    )

    texts = [
        "Product A",
        "Product B",
    ]

    result = embeddings.embed_documents(texts)

    assert len(calls) == 1
    assert calls[0]["texts"] == texts
    assert calls[0]["convert_to_numpy"] is True

    assert len(result) == 2
    assert len(result[0]) == embeddings.EMBEDDING_DIMENSION
    assert len(result[1]) == embeddings.EMBEDDING_DIMENSION


def test_embed_query_empty_input():
    with pytest.raises(
        ValueError,
        match="Query text cannot be empty.",
    ):
        embeddings.embed_query("")


def test_embed_query_whitespace_input():
    with pytest.raises(
        ValueError,
        match="Query text cannot be empty.",
    ):
        embeddings.embed_query("   ")


def test_embed_query_success(monkeypatch):
    class FakeModel:
        def encode_query(self, text, convert_to_numpy):
            assert text == "How much is Jollof Rice?"
            assert convert_to_numpy is True

            return np.array(
                [0.3] * embeddings.EMBEDDING_DIMENSION
            )

    monkeypatch.setattr(
        embeddings,
        "_model",
        FakeModel(),
    )

    result = embeddings.embed_query(
        "How much is Jollof Rice?"
    )

    assert len(result) == 384
    assert result == [0.3] * 384


def test_embed_query_rejects_wrong_dimension(monkeypatch):
    class FakeModel:
        def encode_query(self, text, convert_to_numpy):
            return np.array([0.3] * 100)

    monkeypatch.setattr(
        embeddings,
        "_model",
        FakeModel(),
    )

    with pytest.raises(
        ValueError,
        match="Query embedding must contain exactly 384 dimensions.",
    ):
        embeddings.embed_query("How much is Jollof Rice?")