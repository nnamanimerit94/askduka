"""Ensure owner-facing API never accidentally mounts internal admin endpoints."""
from backend.app.owner_app import app


def test_owner_app_does_not_mount_internal_admin():
    paths = {route.path for route in app.routes if isinstance(getattr(route, 'path', None), str)}
    assert "/admin/dashboard" not in paths
    assert not any(path.startswith("/admin") for path in paths)


def test_owner_app_disables_api_documentation():
    assert app.openapi_url is None
    assert app.docs_url is None
