"""Owner-only, business-scoped conversation summaries."""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.conversation_models import Conversation
from backend.app.owner_auth_api import db_session
from backend.app.owner_business_api import require_business_owner

router = APIRouter(prefix="/api/businesses", tags=["owner-conversations"])


@router.get("/{business_id}/conversations")
def list_conversations(
    business_id: uuid.UUID = Depends(require_business_owner),
    db: Session = Depends(db_session),
):
    rows = db.scalars(
        select(Conversation).where(Conversation.business_id == business_id)
        .order_by(Conversation.updated_at.desc()).limit(100)
    ).all()
    return {"conversations": [
        {"customer_phone": item.customer_phone, "last_message": item.last_message,
         "timestamp": item.updated_at.isoformat()}
        for item in rows
    ]}
