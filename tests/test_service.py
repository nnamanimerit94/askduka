import uuid

import pytest

from backend.app.db.database import SessionLocal
from backend.app.db.repository import create_business
from backend.app.ingestion.service import ingest_document


def test_ingest_document_success(monkeypatch):
    session = SessionLocal()

    business_id = None

    try:
        business = create_business(
            session,
            "AskDuka Service Test Business",
        )

        business_id = business.id
        session.commit()

        fake_embeddings = lambda texts: [
            [0.1] * 384 for _ in texts
        ]

        monkeypatch.setattr(
            "backend.app.ingestion.service.embed_documents",
            fake_embeddings,
        )

        result = ingest_document(
            business_id,
            "tests/fixtures/sample_catalog.txt",
        )

        assert result["business_id"] == str(business_id)
        assert result["filename"] == "sample_catalog.txt"
        assert result["chunks_created"] > 0
        assert result["status"] == "completed"

    finally:
        if business_id:
            session.rollback()

            from backend.app.db.models import Business

            session.query(Business).filter_by(
                id=business_id
            ).delete()

            session.commit()

        session.close()


def test_ingest_document_file_not_found():
    fake_business_id = uuid.uuid4()

    with pytest.raises(FileNotFoundError):
        ingest_document(
            fake_business_id,
            "tests/fixtures/does_not_exist.txt",
        )


def test_ingest_document_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    session = SessionLocal()
    business_id = None

    try:
        business = create_business(
            session,
            "AskDuka Empty File Test Business",
        )

        business_id = business.id
        session.commit()

        with pytest.raises(
            ValueError,
            match="contains no text",
        ):
            ingest_document(
                business_id,
                str(empty_file),
            )

    finally:
        if business_id:
            session.rollback()

            from backend.app.db.models import Business

            session.query(Business).filter_by(
                id=business_id
            ).delete()

            session.commit()

        session.close()


def test_ingest_document_embedding_mismatch(monkeypatch):
    session = SessionLocal()

    business_id = None

    try:
        business = create_business(
            session,
            "AskDuka Mismatch Test Business",
        )

        business_id = business.id
        session.commit()

        monkeypatch.setattr(
            "backend.app.ingestion.service.embed_documents",
            lambda texts: [],
        )

        with pytest.raises(
            ValueError,
            match="does not match",
        ):
            ingest_document(
                business_id,
                "tests/fixtures/sample_catalog.txt",
            )

    finally:
        if business_id:
            session.rollback()

            from backend.app.db.models import Business

            session.query(Business).filter_by(
                id=business_id
            ).delete()

            session.commit()

        session.close()