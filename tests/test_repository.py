from backend.app.db.database import SessionLocal
from backend.app.db.models import (
    Business,
    Document,
    DocumentChunk,
)
from backend.app.db.repository import (
    create_business,
    create_document,
    create_document_chunks,
    get_business,
    get_document,
    get_document_chunks,
    update_document_status,
)


def test_repository_creates_document_data():
    session = SessionLocal()

    business_id = None
    document_id = None

    try:
        business = create_business(
            session,
            "AskDuka Test Business",
        )

        business_id = business.id

        document = create_document(
            session,
            business.id,
            "test_catalog.txt",
            ".txt",
        )

        document_id = document.id

        chunks = [
            "Jollof Rice - ₦2,500",
            "Fried Rice - ₦3,000",
        ]

        embeddings = [
            [0.1] * 384,
            [0.2] * 384,
        ]

        document_chunks = create_document_chunks(
            session,
            document.id,
            chunks,
            embeddings,
        )

        assert business.id is not None
        assert document.id is not None

        assert len(document_chunks) == 2

        assert document_chunks[0].id is not None
        assert document_chunks[1].id is not None

        assert document_chunks[0].chunk_index == 0
        assert document_chunks[1].chunk_index == 1

        assert document_chunks[0].chunk_text == (
            "Jollof Rice - ₦2,500"
        )

        assert document_chunks[1].chunk_text == (
            "Fried Rice - ₦3,000"
        )

        session.commit()

    finally:
        session.rollback()

        if document_id:
            session.query(DocumentChunk).filter_by(
                document_id=document_id
            ).delete()

            session.query(Document).filter_by(
                id=document_id
            ).delete()

        if business_id:
            session.query(Business).filter_by(
                id=business_id
            ).delete()

        session.commit()
        session.close()


def test_repository_reads_and_updates_document_data():
    session = SessionLocal()

    business_id = None
    document_id = None

    try:
        business = create_business(
            session,
            "AskDuka Repository Read Test",
        )

        business_id = business.id

        document = create_document(
            session,
            business.id,
            "catalog.txt",
            ".txt",
        )

        document_id = document.id

        chunks = [
            "Jollof Rice - ₦2,500",
            "Fried Rice - ₦3,000",
        ]

        embeddings = [
            [0.1] * 384,
            [0.2] * 384,
        ]

        create_document_chunks(
            session,
            document.id,
            chunks,
            embeddings,
        )

        session.commit()

        found_business = get_business(
            session,
            business.id,
        )

        found_document = get_document(
            session,
            document.id,
        )

        found_chunks = get_document_chunks(
            session,
            document.id,
        )

        assert found_business is not None
        assert found_business.name == (
            "AskDuka Repository Read Test"
        )

        assert found_document is not None
        assert found_document.filename == "catalog.txt"

        assert len(found_chunks) == 2

        assert found_chunks[0].chunk_index == 0
        assert found_chunks[1].chunk_index == 1

        assert found_chunks[0].chunk_text == (
            "Jollof Rice - ₦2,500"
        )

        assert found_chunks[1].chunk_text == (
            "Fried Rice - ₦3,000"
        )

        updated_document = update_document_status(
            session,
            document.id,
            "processing",
        )

        assert updated_document is not None
        assert updated_document.status == "processing"

        session.commit()

    finally:
        session.rollback()

        if document_id:
            session.query(DocumentChunk).filter_by(
                document_id=document_id
            ).delete()

            session.query(Document).filter_by(
                id=document_id
            ).delete()

        if business_id:
            session.query(Business).filter_by(
                id=business_id
            ).delete()

        session.commit()
        session.close()
