import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.app.webhook.orchestrator import handle_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook")
def verify_webhook(request: Request):
    """
    WhatsApp Cloud API verification handshake.

    Meta calls this once, when the webhook URL is first configured
    in the app dashboard. Echoing hub.challenge as plain text
    confirms we control the endpoint.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        return PlainTextResponse(challenge or "")

    return JSONResponse(
        status_code=403,
        content={"detail": "Webhook verification failed."},
    )


@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Incoming WhatsApp events.

    Always answers 200 so Meta does not re-deliver: a message we
    fail to process is logged and dropped, not retried. Duplicate
    deliveries are filtered by message id in the orchestrator.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"status": "ok"})

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for message in value.get("messages", []):
                try:
                    handle_message(message)
                except Exception:
                    logger.exception(
                        "Failed to handle message %s",
                        message.get("id"),
                    )

    return JSONResponse({"status": "ok"})
