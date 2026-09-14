from fastapi import APIRouter, FastAPI

from backend.app.webhook.router import router as webhook_router

health_router = APIRouter()


@health_router.get("/health")
def health():
    return {"status": "ok"}


def create_app() -> FastAPI:
    app = FastAPI(title="AskDuka API")

    app.include_router(webhook_router)
    app.include_router(health_router)

    return app


app = create_app()
