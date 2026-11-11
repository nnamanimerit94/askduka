"""WhatsApp Cloud API webhook with Meta HMAC signature verification."""
import hmac
import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.app.webhook.orchestrator import handle_message
from backend.app.webhook.signature import valid_meta_signature

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    if verify_token and mode == "subscribe" and token and hmac.compare_digest(token, verify_token):
        return PlainTextResponse(challenge or "")
    return JSONResponse(status_code=403, content={"detail": "Webhook verification failed."})


@router.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.body()
    if not valid_meta_signature(
        body,
        request.headers.get("X-Hub-Signature-256"),
        os.getenv("WHATSAPP_APP_SECRET"),
    ):
        return JSONResponse(status_code=403, content={"detail": "Invalid webhook signature."})

    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON."})
    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"detail": "Invalid payload."})

    entries = payload.get("entry", [])
    if not isinstance(entries, list):
        return JSONResponse(status_code=400, content={"detail": "Invalid entry collection."})

    failed = False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        changes = entry.get("changes", [])
        if not isinstance(changes, list):
            return JSONResponse(status_code=400, content={"detail": "Invalid changes collection."})
        for change in changes:
            if not isinstance(change, dict):
                continue
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue
            # A single-business pilot must never answer events for another number.
            expected_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
            metadata = value.get("metadata")
            actual_phone_id = metadata.get("phone_number_id") if isinstance(metadata, dict) else None
            if expected_phone_id and actual_phone_id != expected_phone_id:
                logger.warning("Ignoring WhatsApp event for an unconfigured phone number")
                continue
            messages = value.get("messages", [])
            if not isinstance(messages, list):
                return JSONResponse(status_code=400, content={"detail": "Invalid messages collection."})
            for message in messages:
                if not isinstance(message, dict):
                    continue
                if message.get("type") == "text":
                    text_payload = message.get("text")
                    if not isinstance(text_payload, dict) or not isinstance(text_payload.get("body"), str):
                        logger.warning("Rejecting malformed WhatsApp text message")
                        return JSONResponse(status_code=400, content={"detail": "Invalid text message."})
                try:
                    handle_message(message)
                except Exception:
                    failed = True
                    logger.exception("Failed to handle message %s", message.get("id"))
    if failed:
        # A non-2xx response allows Meta to redeliver the event.
        return JSONResponse(status_code=503, content={"detail": "Message processing temporarily unavailable."})
    return JSONResponse({"status": "ok"})
