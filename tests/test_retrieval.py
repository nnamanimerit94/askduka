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
    search_document_chunks,
)


def test_search_document_chunks_returns_most_similar():
    session = SessionLocal()

    business_id = None
    document_id = None

    try:
        business = create_business(
            session,
            "AskDuka Retrieval Test Business",
        )

        business_id = business.id

        document = create_document(
            session,
            business.id,
            "retrieval_catalog.txt",
            ".txt",
        )

        document_id = document.id

        chunks = [
            "Jollof Rice - ₦2,500",
            "Fried Rice - ₦3,000",
            "Grilled Chicken - ₦4,500",
        ]

        embeddings = [
            [1.0] + [0.0] * 383,
            [0.9] + [0.1] + [0.0] * 382,
            [0.0] + [1.0] + [0.0] * 382,
        ]

        create_document_chunks(
            session,
            document.id,
            chunks,
            embeddings,
        )

        session.commit()

        query_embedding = [1.0] + [0.0] * 383

        results = search_document_chunks(
            session,
            business.id,
            query_embedding,
            limit=3,
        )

        assert len(results) == 3

        first_chunk, first_score = results[0]

        assert first_chunk.chunk_text == (
            "Jollof Rice - ₦2,500"
        )

        assert first_score > 0.9

        assert results[0][1] >= results[1][1]
        assert results[1][1] >= results[2][1]

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


def test_search_document_chunks_respects_business_isolation():
    session = SessionLocal()

    business_one_id = None
    business_two_id = None
    document_one_id = None
    document_two_id = None

    try:
        business_one = create_business(
            session,
            "AskDuka Retrieval Business One",
        )

        business_two = create_business(
            session,
            "AskDuka Retrieval Business Two",
        )

        business_one_id = business_one.id
        business_two_id = business_two.id

        document_one = create_document(
            session,
            business_one.id,
            "business_one.txt",
            ".txt",
        )

        document_two = create_document(
            session,
            business_two.id,
            "business_two.txt",
            ".txt",
        )

        document_one_id = document_one.id
        document_two_id = document_two.id

        create_document_chunks(
            session,
            document_one.id,
            ["Business One Product"],
            [[1.0] + [0.0] * 383],
        )

        create_document_chunks(
            session,
            document_two.id,
            ["Business Two Product"],
            [[1.0] + [0.0] * 383],
        )

        session.commit()

        query_embedding = [1.0] + [0.0] * 383

        results = search_document_chunks(
            session,
            business_one.id,
            query_embedding,
            limit=5,
        )

        assert len(results) == 1

        chunk, score = results[0]

        assert chunk.chunk_text == "Business One Product"
        assert score > 0.99

    finally:
        session.rollback()

        if document_one_id:
            session.query(DocumentChunk).filter_by(
                document_id=document_one_id
            ).delete()

            session.query(Document).filter_by(
                id=document_one_id
            ).delete()

        if document_two_id:
            session.query(DocumentChunk).filter_by(
                document_id=document_two_id
            ).delete()

            session.query(Document).filter_by(
                id=document_two_id
            ).delete()

        if business_one_id:
            session.query(Business).filter_by(
                id=business_one_id
            ).delete()

        if business_two_id:
            session.query(Business).filter_by(
                id=business_two_id
            ).delete()

        session.commit()
        session.close()


def test_search_document_chunks_empty_embedding():
    session = SessionLocal()

    try:
        results = search_document_chunks(
            session,
            None,
            [],
        )

        assert results == []

    finally:
        session.close()


def test_search_document_chunks_rejects_wrong_dimension():
    session = SessionLocal()

    try:
        try:
            search_document_chunks(
                session,
                None,
                [0.1] * 512,
            )

            assert False, "Expected ValueError"

        except ValueError as exc:
            assert "384 dimensions" in str(exc)

    finally:
        session.close()


def test_search_document_chunks_rejects_invalid_limit():
    session = SessionLocal()

    try:
        try:
            search_document_chunks(
                session,
                None,
                [0.1] * 384,
                limit=0,
            )

            assert False, "Expected ValueError"

        except ValueError as exc:
            assert "greater than zero" in str(exc)

    finally:
        session.close()