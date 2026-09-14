from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db.models import (
    Business,
    Document,
    DocumentChunk,
)


def create_business(
    session: Session,
    name: str,
) -> Business:
    business = Business(
        name=name,
    )

    session.add(business)
    session.flush()

    return business


def create_document(
    session: Session,
    business_id,
    filename: str,
    file_type: str,
) -> Document:
    document = Document(
        business_id=business_id,
        filename=filename,
        file_type=file_type,
    )

    session.add(document)
    session.flush()

    return document


def create_document_chunks(
    session: Session,
    document_id,
    chunks: list[str],
    embeddings: list[list[float]],
) -> list[DocumentChunk]:
    document_chunks = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):
        document_chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            chunk_text=chunk,
            embedding=embedding,
        )

        session.add(document_chunk)
        document_chunks.append(document_chunk)

    session.flush()

    return document_chunks


def get_business(
    session: Session,
    business_id,
) -> Business | None:
    return (
        session.query(Business)
        .filter(Business.id == business_id)
        .first()
    )


def get_document(
    session: Session,
    document_id,
) -> Document | None:
    return (
        session.query(Document)
        .filter(Document.id == document_id)
        .first()
    )


def get_document_chunks(
    session: Session,
    document_id,
) -> list[DocumentChunk]:
    return (
        session.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id
        )
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


def update_document_status(
    session: Session,
    document_id,
    status: str,
) -> Document | None:
    document = get_document(
        session,
        document_id,
    )

    if document is None:
        return None

    document.status = status

    session.flush()

    return document


def search_document_chunks(
    session: Session,
    business_id,
    query_embedding: list[float],
    limit: int = 5,
) -> list[tuple[DocumentChunk, float]]:
    """
    Search document chunks using cosine similarity.

    Returns:
        A list of (DocumentChunk, similarity_score) tuples,
        ordered from most relevant to least relevant.
    """

    if not query_embedding:
        return []

    if len(query_embedding) != 384:
        raise ValueError(
            "Query embedding must contain exactly 384 dimensions."
        )

    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero."
        )

    embedding_text = "[" + ",".join(
        str(value) for value in query_embedding
    ) + "]"

    query = text(
        """
        SELECT
            dc.id,
            1 - (
                dc.embedding <=> CAST(:query_embedding AS vector)
            ) AS similarity
        FROM document_chunks AS dc
        JOIN documents AS d
            ON d.id = dc.document_id
        WHERE d.business_id = :business_id
          AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """
    )

    rows = session.execute(
        query,
        {
            "query_embedding": embedding_text,
            "business_id": business_id,
            "limit": limit,
        },
    ).all()

    if not rows:
        return []

    chunk_ids = [row.id for row in rows]

    chunks = (
        session.query(DocumentChunk)
        .filter(DocumentChunk.id.in_(chunk_ids))
        .all()
    )

    chunks_by_id = {
        chunk.id: chunk
        for chunk in chunks
    }

    results = []

    for row in rows:
        chunk = chunks_by_id.get(row.id)

        if chunk is not None:
            results.append(
                (
                    chunk,
                    float(row.similarity),
                )
            )

    return results