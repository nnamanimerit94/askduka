import sys
import types
from unittest.mock import MagicMock
import pytest
from backend.app.owner_document_indexing import index_uploaded_chunks, vector_indexing_enabled


def test_indexing_off_by_default(monkeypatch):
    monkeypatch.delenv("ASKDUKA_ENABLE_UPLOAD_EMBEDDINGS", raising=False)
    assert vector_indexing_enabled() is False


def test_valid_embeddings_are_written_in_transaction(monkeypatch):
    fake = types.ModuleType("backend.app.ingestion.embeddings")
    fake.embed_documents = lambda texts: [[0.1] * 384 for _ in texts]
    monkeypatch.setitem(sys.modules, "backend.app.ingestion.embeddings", fake)
    db = MagicMock()
    chunk = MagicMock(chunk_text="sample", id="chunk-1")
    index_uploaded_chunks(db, [chunk])
    assert db.execute.call_count == 1
    assert db.execute.call_args.args[1]["chunk_id"] == "chunk-1"
    assert db.execute.call_args.args[1]["embedding"].startswith("[0.1,")


def test_invalid_dimensions_rejected(monkeypatch):
    fake = types.ModuleType("backend.app.ingestion.embeddings")
    fake.embed_documents = lambda texts: [[0.1] * 3 for _ in texts]
    monkeypatch.setitem(sys.modules, "backend.app.ingestion.embeddings", fake)
    db = MagicMock()
    with pytest.raises(ValueError, match="384"):
        index_uploaded_chunks(db, [MagicMock(chunk_text="sample")])
    db.execute.assert_not_called()
