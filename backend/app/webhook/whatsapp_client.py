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
