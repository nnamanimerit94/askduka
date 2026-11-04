"""Authenticated business catalog management API.

Not mounted on the public preview app. Database sessions are initialized
only when this router is included in a configured production application.
"""
import hmac
import os
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.models import Business, Document, DocumentChunk

router = APIRouter(prefix="/admin", tags=["business-management"])


def admin_auth(x_admin_key: str | None = Header(default=None)):
    expected = os.getenv("ASKDUKA_ADMIN_API_KEY")
    if not expected or not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


def db_session():
    from backend.app.db.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class CatalogCreate(BaseModel):
    filename: str = Field(default="catalog.txt", min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=50000)


@router.post("/businesses", dependencies=[Depends(admin_auth)], status_code=201)
def add_business(request: BusinessCreate, db: Session = Depends(db_session)):
    name = request.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Business name too short")
    business = Business(name=name)
    db.add(business)
    db.commit()
    db.refresh(business)
    return {"id": str(business.id), "name": business.name}


@router.post("/businesses/{business_id}/catalog", dependencies=[Depends(admin_auth)], status_code=201)
def add_catalog(business_id: uuid.UUID, request: CatalogCreate, db: Session = Depends(db_session)):
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    lines = [line.strip() for line in request.content.splitlines() if line.strip()]
    if not lines or len(lines) > 300:
        raise HTTPException(status_code=422, detail="Catalog must contain 1–300 nonempty lines")
    document = Document(
        business_id=business_id,
        filename=request.filename,
        file_type="txt",
        status="ready_for_embedding",
    )
    db.add(document)
    db.flush()
    for index, line in enumerate(lines):
        db.add(DocumentChunk(document_id=document.id, chunk_index=index, chunk_text=line))
    db.commit()
    return {"document_id": str(document.id), "business_id": str(business_id),
            "lines_saved": len(lines), "status": "ready_for_embedding"}


@router.get("/businesses/{business_id}/catalog", dependencies=[Depends(admin_auth)])
def list_catalog(business_id: uuid.UUID, db: Session = Depends(db_session)):
    if db.get(Business, business_id) is None:
        raise HTTPException(status_code=404, detail="Business not found")
    rows = (
        db.query(DocumentChunk.chunk_text)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.business_id == business_id)
        .order_by(Document.created_at, DocumentChunk.chunk_index)
        .all()
    )
    return {"business_id": str(business_id), "lines": [row[0] for row in rows]}
