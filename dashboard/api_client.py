import os

import requests
from dotenv import load_dotenv


load_dotenv()

API_URL = os.getenv(
    "BACKEND_API_URL",
    "http://localhost:8000",
)


class APIError(Exception):
    """Raised when the AskDuka API returns an error."""


def login(email: str, password: str) -> dict:
    """Login the business owner."""

    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise APIError(
            "Could not connect to the AskDuka backend."
        ) from exc

    if not response.ok:
        raise APIError(
            f"Login failed: {response.status_code}"
        )

    return response.json()


def upload_document(file, token: str) -> dict:
    """Upload a business document."""

    try:
        response = requests.post(
            f"{API_URL}/api/documents",
            headers={
                "Authorization": f"Bearer {token}",
            },
            files={
                "file": (
                    file.name,
                    file,
                    file.type,
                )
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        raise APIError(
            "Could not connect to the AskDuka backend."
        ) from exc

    if not response.ok:
        raise APIError(
            f"Document upload failed: {response.status_code}"
        )

    return response.json()


def get_conversations(token: str) -> dict:
    """Get customer conversations."""

    try:
        response = requests.get(
            f"{API_URL}/api/conversations",
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise APIError(
            "Could not connect to the AskDuka backend."
        ) from exc

    if not response.ok:
        raise APIError(
            f"Could not retrieve conversations: "
            f"{response.status_code}"
        )

    return response.json()


def current_owner(token: str) -> dict:
    """Validate the bearer token against the backend."""
    try:
        response = requests.get(
            f"{API_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise APIError("Could not verify your session.") from exc
    if not response.ok:
        raise APIError(f"Session verification failed: {response.status_code}")
    return response.json()


def revoke_session(token: str) -> None:
    """Revoke the server-side session before clearing local state."""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise APIError("Could not contact the server to log out.") from exc
    if not response.ok:
        raise APIError(f"Logout failed: {response.status_code}")
