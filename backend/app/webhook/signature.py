"""Verify signed Meta webhook requests before processing events."""
import hashlib
import hmac


def valid_meta_signature(body: bytes, header: str | None, secret: str | None) -> bool:
    if not secret or not header or not header.startswith("sha256="):
        return False
    digest = header[len("sha256="):]
    if len(digest) != 64:
        return False
    try:
        bytes.fromhex(digest)
    except ValueError:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, digest.lower())
