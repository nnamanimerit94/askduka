"""Owner identity and business membership authorization primitives.

No public login or token issuance is enabled by this module.
Passwords must never be stored in plaintext; use scrypt with per-user salt.
"""
import hashlib
import hmac
import os
import uuid


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1$" + salt.hex() + "$" + digest.hex()


def verify_password(password: str, encoded: str) -> bool:
    if not isinstance(password, str) or not isinstance(encoded, str):
        return False
    try:
        algorithm, n, r, p, salt_hex, digest_hex = encoded.split("$")
        if (algorithm, n, r, p) != ("scrypt", "16384", "8", "1"):
            return False
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex)
        if len(salt) != 16 or len(expected) != 64:
            return False
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, OverflowError):
        return False


def has_business_access(user_id: uuid.UUID, business_id: uuid.UUID, memberships) -> bool:
    """Deny by default; only explicit active owner membership grants access."""
    if not isinstance(user_id, uuid.UUID) or not isinstance(business_id, uuid.UUID):
        return False
    return any(
        getattr(member, "user_id", None) == user_id
        and getattr(member, "business_id", None) == business_id
        and getattr(member, "role", None) == "owner"
        and getattr(member, "is_active", False) is True
        for member in memberships
    )
