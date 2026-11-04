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

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue
            for message in value.get("messages", []):
                if not isinstance(message, dict):
                    continue
                try:
                    handle_message(message)
                except Exception:
                    logger.exception("Failed to handle message %s", message.get("id"))
    return JSONResponse({"status": "ok"})
