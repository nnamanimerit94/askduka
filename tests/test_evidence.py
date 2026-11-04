from types import SimpleNamespace

from backend.app.evidence import prepare_generation_context


def test_orm_chunks_are_converted_to_generation_input():
    chunk = SimpleNamespace(chunk_text="Wig costs NGN 50000", document_id="doc-1")
    assert prepare_generation_context([{"chunk": chunk, "similarity": 0.8}]) == [
        {"chunk_text": "Wig costs NGN 50000", "source_document": "doc-1"}
    ]


def test_empty_and_invalid_evidence_is_discarded():
    data = [
        {"chunk": SimpleNamespace(chunk_text="  ")},
        {"chunk": SimpleNamespace(chunk_text="Valid catalog line", document_id="doc-2"), "similarity": -1},
        {"chunk": SimpleNamespace(chunk_text="Delivery in 2 days", document_id="doc-3"), "similarity": 0.6},
    ]
    assert prepare_generation_context(data) == [
        {"chunk_text": "Delivery in 2 days", "source_document": "doc-3"}
    ]


def test_evidence_limit():
    results = [
        {"chunk": SimpleNamespace(chunk_text=str(i), document_id=i)}
        for i in range(10)
    ]
    assert len(prepare_generation_context(results, limit=3)) == 3
