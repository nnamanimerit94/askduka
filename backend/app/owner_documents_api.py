"""Read-only business document listing protected by active owner membership."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Document
from backend.app.owner_auth_api import db_session
from backend.app.owner_business_api import require_business_owner


router = APIRouter(prefix="/api/businesses", tags=["owner-documents"])


@router.get("/{business_id}/documents")
def list_business_documents(
    business_id: uuid.UUID = Depends(require_business_owner),
    db: Session = Depends(db_session),
):
    documents = db.scalars(
        select(Document)
        .where(Document.business_id == business_id)
        .order_by(Document.created_at.desc())
    ).all()
    return {
        "documents": [
            {
                "document_id": str(doc.id),
                "filename": doc.filename,
                "file_type": doc.file_type,
                "status": doc.status,
            }
            for doc in documents
        ]
    }
