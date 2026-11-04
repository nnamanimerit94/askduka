import hashlib
import hmac

from backend.app.webhook.router import valid_meta_signature


def test_signature_valid():
    secret = "test-app-secret"
    body = b'{"entry":[]}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert valid_meta_signature(body, "sha256=" + signature, secret)


def test_signature_rejects_modified_body():
    secret = "test-app-secret"
    body = b'{"entry":[]}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert not valid_meta_signature(body + b" ", "sha256=" + signature, secret)


def test_signature_rejects_missing_secret_or_header():
    assert not valid_meta_signature(b"{}", None, "secret")
    assert not valid_meta_signature(b"{}", "sha256=" + "0" * 64, None)


def test_signature_rejects_invalid_digest():
    assert not valid_meta_signature(b"{}", "sha256=not-hex", "secret")
