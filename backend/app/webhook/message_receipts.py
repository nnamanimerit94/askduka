"""Database primitives for durable inbound WhatsApp message receipts.

Opt-in webhook integration requires migration 006 and ASKDUKA_USE_DURABLE_RECEIPTS=true.
"""
import uuid

from sqlalchemy import text


def claim_message(session, business_id: uuid.UUID, message_id: str) -> bool:
    """Atomically claim a previously unseen message across workers.

    Atomically reclaims explicitly failed receipts, incrementing attempts.
    Returns False for processing or sent receipts. Abandoned processing
    leases and crash recovery are intentionally not implemented.
    """
    if not isinstance(business_id, uuid.UUID) or not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("A valid business UUID and nonempty provider message ID are required")
    result = session.execute(
        text("""
            INSERT INTO whatsapp_message_receipts
                (business_id, message_id, status, attempts)
            VALUES (:business_id, :message_id, 'processing', 1)
            ON CONFLICT (business_id, message_id) DO UPDATE
            SET status = 'processing',
                attempts = whatsapp_message_receipts.attempts + 1,
                updated_at = NOW()
            WHERE whatsapp_message_receipts.status = 'failed'
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
    """Record a failed attempt so a later delivery can atomically reclaim it."""
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


def receipt_status(session, business_id: uuid.UUID, message_id: str) -> str | None:
    """Read a receipt after a claim conflict; unknown status must not be acknowledged."""
    return session.execute(
        text("""
            SELECT status FROM whatsapp_message_receipts
            WHERE business_id = :business_id AND message_id = :message_id
        """),
        {"business_id": business_id, "message_id": message_id},
    ).scalar_one_or_none()


def list_stale_processing_receipts(session, older_than_minutes: int = 15, limit: int = 100):
    """Read-only operational view of potentially abandoned receipts.

    No automatic retry is safe: a WhatsApp send may have succeeded before
    the worker crashed without persisting its sent status.
    """
    if type(older_than_minutes) is not int or older_than_minutes < 1:
        raise ValueError("older_than_minutes must be a positive integer")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    return session.execute(
        text("""
            SELECT business_id, message_id, attempts, created_at, updated_at
            FROM whatsapp_message_receipts
            WHERE status = 'processing'
              AND updated_at < NOW() - (:minutes * INTERVAL '1 minute')
            ORDER BY updated_at ASC
            LIMIT :limit
        """),
        {"minutes": older_than_minutes, "limit": limit},
    ).mappings().all()
