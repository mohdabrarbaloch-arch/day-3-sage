"""Summarization endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.limiter import limiter
from app.models import Document, User
from app.schemas import SummarizeRequest, SummarizeResponse
from app.services.summarizer import summarize

router = APIRouter(prefix="/api/summarize", tags=["summarize"])


@router.post("", response_model=SummarizeResponse)
@limiter.limit("20/minute")
def summarize_document(
    request: Request,
    payload: SummarizeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.get(Document, payload.document_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    summary = summarize(doc.content, ratio=payload.ratio, max_sentences=payload.max_sentences)
    if not summary:
        raise HTTPException(status_code=422, detail="Document has no summarizable text")
    original_sentences = doc.content.count(". ") + 1
    summary_sentences = summary.count(". ") + 1
    return SummarizeResponse(
        document_id=doc.id,
        summary=summary,
        sentence_count=summary_sentences,
        compression_ratio=round(summary_sentences / max(original_sentences, 1), 4),
        grounded=True,
    )
