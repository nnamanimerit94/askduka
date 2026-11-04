"""Opt-in integration test against a dedicated AskDuka test database.

Run with ASKDUKA_TEST_DATABASE_URL set to a disposable PostgreSQL database
with the AskDuka schema installed. This test intentionally writes records.
Never point it at a production database.
"""
import os
import uuid

import pytest


@pytest.mark.skipif(
    not os.getenv("ASKDUKA_TEST_DATABASE_URL"),
    reason="Dedicated test database not configured",
)
def test_create_and_read_catalog_with_postgres():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from backend.app.db.models import Business, Document, DocumentChunk

    url = os.environ["ASKDUKA_TEST_DATABASE_URL"]
    if "askduka_test" not in url.lower():
        pytest.fail("Refusing to write: test database URL must contain askduka_test")
    engine = create_engine(url, pool_pre_ping=True)
    with Session(engine) as session:
        transaction = session.begin()
        try:
            business = Business(id=uuid.uuid4(), name="Integration Test Shop")
            session.add(business)
            session.flush()
            document = Document(
                id=uuid.uuid4(), business_id=business.id,
                filename="catalog.txt", file_type="txt",
                status="ready_for_embedding",
            )
            session.add(document)
            session.flush()
            session.add(DocumentChunk(
                id=uuid.uuid4(), document_id=document.id,
                chunk_index=0, chunk_text="Blue dress: ₦15000",
            ))
            session.flush()
            stored = (
                session.query(DocumentChunk.chunk_text)
                .join(Document, Document.id == DocumentChunk.document_id)
                .filter(Document.business_id == business.id)
                .one()
            )
            assert stored[0] == "Blue dress: ₦15000"
        finally:
            transaction.rollback()
    engine.dispose()
