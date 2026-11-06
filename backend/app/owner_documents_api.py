"""Read-only business document listing protected by active owner membership."""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Document, DocumentChunk
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


MAX_TEXT_BYTES = 256 * 1024


@router.post("/{business_id}/documents", status_code=201)
async def upload_business_text_document(
    business_id: uuid.UUID = Depends(require_business_owner),
    file: UploadFile = File(...),
    db: Session = Depends(db_session),
):
    """Store small UTF-8 text documents in the existing database-backed chunks.

    PDF/DOCX extraction is intentionally not supported by this endpoint yet.
    """
    filename = (file.filename or "").strip()
    if not filename or len(filename) > 255 or "/" in filename or chr(92) in filename or not filename.lower().endswith(".txt"):
        raise HTTPException(status_code=422, detail="Only .txt documents with safe filenames are supported")
    payload = await file.read(MAX_TEXT_BYTES + 1)
    if len(payload) > MAX_TEXT_BYTES:
        raise HTTPException(status_code=413, detail="Text document exceeds 256 KiB limit")
    try:
        content = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Document must be UTF-8 text") from exc
    if not content.strip():
        raise HTTPException(status_code=422, detail="Document is empty")
    document = Document(business_id=business_id, filename=filename, file_type="txt", status="ready")
    db.add(document)
    db.flush()
    for index, offset in enumerate(range(0, len(content), 1500)):
        db.add(DocumentChunk(document_id=document.id, chunk_index=index, chunk_text=content[offset:offset + 1500], chunk_metadata={}))
    db.commit()
    return {"document_id": str(document.id), "status": "ready"}
