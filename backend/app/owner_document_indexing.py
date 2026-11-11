"""Optional synchronous embedding of owner-uploaded text chunks.

This first vertical slice is disabled by default; enable only in an isolated
environment with sentence-transformers and pgvector installed.
"""
import math
import os
from sqlalchemy import text


def vector_indexing_enabled() -> bool:
    return os.getenv("ASKDUKA_ENABLE_UPLOAD_EMBEDDINGS") == "true"


def index_uploaded_chunks(db, chunks) -> None:
    """Embed each chunk and store a pgvector-compatible 384-dimensional vector.

    Runs within the caller's transaction so failures roll back the upload.
    """
    if not chunks:
        raise ValueError("Cannot index an empty document")
    from backend.app.ingestion.embeddings import embed_documents

    vectors = embed_documents([chunk.chunk_text for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding count does not match chunk count")
    for chunk, vector in zip(chunks, vectors):
        if len(vector) != 384 or any(not math.isfinite(float(v)) for v in vector):
            raise ValueError("Expected 384 finite embedding dimensions")
        vector_literal = "[" + ",".join(str(float(v)) for v in vector) + "]"
        db.execute(
            text("UPDATE document_chunks SET embedding = CAST(:embedding AS vector) WHERE id = :chunk_id"),
            {"embedding": vector_literal, "chunk_id": chunk.id},
        )
