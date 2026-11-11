import os

import httpx

GRAPH_API_URL = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v22.0"


def send_text_message(to: str, body: str) -> dict:
    """
    Send a plain-text WhatsApp reply through the Cloud API.
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    api_version = os.getenv("WHATSAPP_API_VERSION", DEFAULT_API_VERSION)

    if not access_token or not access_token.strip():
        raise ValueError("WHATSAPP_ACCESS_TOKEN must be configured")
    if not phone_number_id or not phone_number_id.strip():
        raise ValueError("WHATSAPP_PHONE_NUMBER_ID must be configured")
    if not to or not to.strip():
        raise ValueError("WhatsApp recipient must be provided")
    if not body or not body.strip():
        raise ValueError("WhatsApp message body must be provided")

    url = f"{GRAPH_API_URL}/{api_version}/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }

    headers = {"Authorization": f"Bearer {access_token}"}

    response = httpx.post(
        url,
        json=payload,
        headers=headers,
        timeout=10.0,
    )
    response.raise_for_status()

    return response.json()
