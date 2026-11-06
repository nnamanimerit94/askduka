"""Owner-only API entry point for isolated testing; excludes internal admin router.

Do not expose publicly until session security, signup abuse controls, migration
readiness and deployment network controls have been reviewed.
"""
from fastapi import FastAPI

from backend.app.owner_auth_api import router as auth_router
from backend.app.owner_business_api import router as business_router
from backend.app.owner_documents_api import router as documents_router

app = FastAPI(
    title="AskDuka Owner API (Private Test)",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(documents_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "askduka-owner-private"}
