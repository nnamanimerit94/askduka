"""Safe deployment entry point for AskDuka's pre-production API.

The WhatsApp webhook and AI retrieval pipeline are intentionally not exposed
until credentials, database migrations, request signature verification, and
end-to-end tests have been completed.
"""
from fastapi import FastAPI

app = FastAPI(
    title="AskDuka API — Development Preview",
    description="Pre-production status API. Customer messaging is not enabled.",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "name": "AskDuka",
        "environment": "development-preview",
        "status": "backend_online",
        "customer_messaging_enabled": False,
        "message": "AskDuka is under development. WhatsApp and AI responses are not live.",
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "askduka-preview"}

@app.get("/readiness")
def readiness():
    return {
        "ready_for_customers": False,
        "pending": [
            "database provisioning and migration",
            "document ingestion API and dashboard",
            "grounded AI generation",
            "WhatsApp webhook signature verification",
            "end-to-end tests",
        ],
    }
