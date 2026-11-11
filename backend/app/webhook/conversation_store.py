"""Persist the latest customer message for an explicitly configured business.

Opt-in until migrations and webhook deployment have been reviewed.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from backend.app.db.conversation_models import Conversation

logger = logging.getLogger(__name__)


def record_incoming_message(business_id: uuid.UUID, customer_phone: str, text: str) -> None:
    if os.getenv("ASKDUKA_STORE_CONVERSATIONS") != "true":
        return
    if not customer_phone or not text:
        return
    # Import only when enabled, so existing webhook tests and preview do not
    # require a database connection.
    from backend.app.db.database import SessionLocal
    with SessionLocal() as db:
        statement = insert(Conversation).values(
            id=uuid.uuid4(),
            business_id=business_id,
            customer_phone=customer_phone,
            last_message=text,
            updated_at=datetime.now(timezone.utc),
        )
        statement = statement.on_conflict_do_update(
            constraint="uq_conversations_business_customer",
            set_={
                "last_message": statement.excluded.last_message,
                "updated_at": statement.excluded.updated_at,
            },
        )
        db.execute(statement)
        db.commit()
