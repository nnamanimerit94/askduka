"""Database primitives for durable inbound WhatsApp message receipts.

Not yet wired into the webhook. Requires migration 006.
"""
import uuid

from sqlalchemy import text


def claim_message(session, business_id: uuid.UUID, message_id: str) -> bool:
    """Atomically claim a previously unseen message across workers.

    Returns False for any existing receipt (including failed receipts).
    Retrying failed claims and lease recovery are intentionally not implemented.
    """
    if not isinstance(business_id, uuid.UUID) or not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("A valid business UUID and nonempty provider message ID are required")
    result = session.execute(
        text("""
            INSERT INTO whatsapp_message_receipts
                (business_id, message_id, status, attempts)
            VALUES (:business_id, :message_id, 'processing', 1)
            ON CONFLICT (business_id, message_id) DO NOTHING
            RETURNING message_id
        """),
        {"business_id": business_id, "message_id": message_id},
    )
    return result.scalar_one_or_none() is not None


def mark_sent(session, business_id: uuid.UUID, message_id: str) -> bool:
    """Mark a claimed message sent; caller owns transaction/commit."""
    result = session.execute(
        text("""
            UPDATE whatsapp_message_receipts
            SET status = 'sent', updated_at = NOW()
            WHERE business_id = :business_id AND message_id = :message_id
              AND status = 'processing'
            RETURNING message_id
        """),
        {"business_id": business_id, "message_id": message_id},
    )
    return result.scalar_one_or_none() is not None


def mark_failed(session, business_id: uuid.UUID, message_id: str) -> bool:
    """Record a failed attempt; retry/reclaim policy is future work."""
    result = session.execute(
        text("""
            UPDATE whatsapp_message_receipts
            SET status = 'failed', updated_at = NOW()
            WHERE business_id = :business_id AND message_id = :message_id
              AND status = 'processing'
            RETURNING message_id
        """),
        {"business_id": business_id, "message_id": message_id},
    )
    return result.scalar_one_or_none() is not None
