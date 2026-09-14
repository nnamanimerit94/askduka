import uuid

import pytest

from backend.app import retrieval


def test_retrieve_success(monkeypatch):
    business_id = uuid.uuid4()

    expected_embedding = [0.5] * 384

    monkeypatch.setattr(
        retrieval,
        "embed_query",
        lambda query: expected_embedding,
    )

    calls = []

    def fake_search(
        session,
        received_business_id,
        query_embedding,
        limit,
    ):
        calls.append(
            {
                "business_id": received_business_id,
                "query_embedding": query_embedding,
                "limit": limit,
            }
        )

        return [
            (
                "chunk-one",
                0.95,
            ),
            (
                "chunk-two",
                0.82,
            ),
        ]

    monkeypatch.setattr(
        retrieval,
        "search_document_chunks",
        fake_search,
    )

    result = retrieval.retrieve(
        business_id,
        "How much is Jollof Rice?",
        limit=5,
    )

    assert len(result) == 2

    assert result[0]["chunk"] == "chunk-one"
    assert result[0]["similarity"] == 0.95

    assert result[1]["chunk"] == "chunk-two"
    assert result[1]["similarity"] == 0.82

    assert len(calls) == 1
    assert calls[0]["business_id"] == business_id
    assert calls[0]["query_embedding"] == expected_embedding
    assert calls[0]["limit"] == 5


def test_retrieve_rejects_empty_query():
    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        retrieval.retrieve(
            uuid.uuid4(),
            "",
        )


def test_retrieve_rejects_whitespace_query():
    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        retrieval.retrieve(
            uuid.uuid4(),
            "   ",
        )


def test_retrieve_rejects_invalid_limit():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        retrieval.retrieve(
            uuid.uuid4(),
            "How much is Jollof Rice?",
            limit=0,
        )
