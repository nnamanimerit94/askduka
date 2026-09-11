from pathlib import Path
import uuid

from backend.app.db.database import SessionLocal
from backend.app.db.repository import (
    create_document,
    create_document_chunks,
)
from backend.app.ingestion.chunker import chunk_text
from backend.app.ingestion.embeddings import embed_documents
from backend.app.ingestion.parser import extract_text


def ingest_document(
    business_id: uuid.UUID,
    file_path: str,
) -> dict:
    """
    Ingest a document for an existing business.

    Pipeline:
        File → Text → Chunks → Embeddings → PostgreSQL

    Document lifecycle:
        pending → processing → completed
                           ↘ failed
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    session = SessionLocal()

    document = None

    try:
        document = create_document(
            session,
            business_id,
            path.name,
            path.suffix.lower(),
        )

        document.status = "processing"
        session.flush()

        text = extract_text(file_path)

        if not text:
            raise ValueError("Document contains no text.")

        chunks = chunk_text(text)

        if not chunks:
            raise ValueError("Document produced no chunks.")

        embeddings = embed_documents(chunks)

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks does not match number of embeddings."
            )

        document_chunks = create_document_chunks(
            session,
            document.id,
            chunks,
            embeddings,
        )

        document.status = "completed"

        session.commit()

        return {
            "business_id": str(business_id),
            "document_id": str(document.id),
            "filename": document.filename,
            "chunks_created": len(document_chunks),
            "status": document.status,
        }

    except Exception:
        session.rollback()

        if document is not None:
            try:
                document.status = "failed"
                session.commit()
            except Exception:
                session.rollback()

        raise

    finally:
        session.close()