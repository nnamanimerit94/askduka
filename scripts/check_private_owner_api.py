"""Read-only smoke check for a locally bound AskDuka owner API.

Run: python scripts/check_private_owner_api.py
Never sends credentials or creates accounts.
"""
import os
from urllib.parse import urlsplit

import requests


def main() -> None:
    base = os.getenv("ASKDUKA_OWNER_TEST_URL", "http://127.0.0.1:8001").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("Refusing to probe non-local owner API; use localhost HTTP only.")
    health = requests.get(f"{base}/health", timeout=5)
    health.raise_for_status()
    assert health.json().get("service") == "askduka-owner-private", "Wrong app: not owner-only API"
    for path in ("/admin", "/admin/dashboard", "/openapi.json", "/docs"):
        response = requests.get(f"{base}{path}", timeout=5)
        assert response.status_code == 404, f"Unexpected exposed path: {path}"
    response = requests.get(f"{base}/api/businesses", timeout=5)
    assert response.status_code == 401, "Unauthenticated business listing must be denied"
    print("PASS: owner-only app, no admin/docs endpoints, unauthenticated business access denied.")


if __name__ == "__main__":
    main()
