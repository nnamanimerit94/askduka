import uuid

from backend.app.db.database import SessionLocal
from backend.app.db.models import DocumentChunk
from backend.app.db.repository import search_document_chunks
from backend.app.ingestion.embeddings import embed_query


def retrieve(
    business_id: uuid.UUID,
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a user query.

    Pipeline:
        Query → Embedding → Vector Search → Results
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    query_embedding = embed_query(query)

    session = SessionLocal()

    try:
        results = search_document_chunks(
            session,
            business_id,
            query_embedding,
            limit=limit,
        )

        return [
            {
                "chunk": chunk,
                "similarity": similarity,
            }
            for chunk, similarity in results
        ]

    finally:
        session.close()
