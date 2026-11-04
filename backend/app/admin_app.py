"""Internal AskDuka administration application.

Run separately from the public preview using:
    uvicorn backend.app.admin_app:app --host 127.0.0.1 --port 8001

Never expose this service publicly without a proper login, per-business
authorization, rate limits, HTTPS and deployment security review.
"""
from fastapi import FastAPI
from backend.app.catalog_api import router as catalog_router

app = FastAPI(
    title="AskDuka Internal Administration",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(catalog_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "askduka-internal-admin"}
