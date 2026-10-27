"""Document endpoints: upload, list, detail, delete."""

import os

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import get_current_user, get_db
from app.limiter import limiter
from app.models import Document, User
from app.schemas import DocumentDetail, DocumentOut
from app.services.extraction import ExtractionError, extract_text

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()


def _validate_upload(filename: str | None, data: bytes) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise HTTPException(status_code=400, detail=f"Unsupported type. Allowed: {allowed}")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the size limit")
    return ext


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = await file.read()
    _validate_upload(file.filename, data)
    try:
        content = extract_text(file.filename or "", data)
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    title = os.path.splitext(file.filename or "untitled")[0]
    doc = Document(
        owner_id=user.id,
        title=title,
        filename=file.filename or "untitled",
        content=content,
        char_count=len(content),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.scalars(
        select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc())
    ).all()
    return list(docs)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    doc = db.get(Document, document_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    doc = db.get(Document, document_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(doc)
    db.commit()
