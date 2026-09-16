import logging
import os
import uuid

from backend.app.generation import generate_answer
from backend.app.retrieval import retrieve
from backend.app.webhook.whatsapp_client import send_text_message

logger = logging.getLogger(__name__)

# In-memory de-duplication of WhatsApp message ids. Meta re-delivers
# events it does not consider acknowledged, so the same message can
# arrive more than once. Single-process MVP only — a second worker
# (e.g. on Render) would need shared storage for this.
_seen_message_ids: set[str] = set()
_SEEN_MESSAGE_IDS_LIMIT = 1000


def handle_message(message: dict) -> None:
    """
    Process one incoming WhatsApp message.

    Pipeline:
        Message → De-duplicate → Retrieve → Generate → Reply

    Only plain text messages are answered in the MVP; anything else
    (images, voice notes, status updates) is acknowledged and ignored.
    """
    message_id = message.get("id")

    if message_id in _seen_message_ids:
        return

    _remember_message_id(message_id)

    if message.get("type") != "text":
        return

    customer_phone = message.get("from")
    customer_message = (message.get("text") or {}).get("body", "")
    customer_message = customer_message.strip()

    if not customer_message:
        return

    business_id = _get_business_id()

    if business_id is None:
        logger.error(
            "ASKDUKA_BUSINESS_ID is not set to a valid UUID; "
            "cannot answer incoming messages."
        )
        return

    results = retrieve(business_id, customer_message)

    chunk_results = [
        {
            "chunk_text": result["chunk"].chunk_text,
            "similarity": result["similarity"],
            "source_document": result["chunk"].document.filename,
        }
        for result in results
    ]

    answer_result = generate_answer(customer_message, chunk_results)

    send_text_message(customer_phone, answer_result["answer"])


def _remember_message_id(message_id) -> None:
    if message_id is None:
        return

    if len(_seen_message_ids) >= _SEEN_MESSAGE_IDS_LIMIT:
        _seen_message_ids.clear()

    _seen_message_ids.add(message_id)


def _get_business_id() -> uuid.UUID | None:
    """
    The MVP serves a single business; which one is configured
    through the environment rather than resolved per message.
    """
    raw = os.getenv("ASKDUKA_BUSINESS_ID")

    if not raw:
        return None

    try:
        return uuid.UUID(raw)

    except ValueError:
        logger.error(
            "ASKDUKA_BUSINESS_ID is not a valid UUID: %s",
            raw,
        )
        return None
