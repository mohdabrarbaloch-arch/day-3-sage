"""Conversation + grounded Q&A endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_current_user, get_db
from app.limiter import limiter
from app.models import Conversation, Document, Message, User
from app.schemas import AnswerResponse, AskRequest, Citation, ConversationDetail, ConversationOut
from app.services.guardrails import flag_question
from app.services.retrieval import answer as retrieve_answer

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _get_owned_document(db: Session, document_id: str, user: User) -> Document:
    doc = db.get(Document, document_id)
    if not doc or doc.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get("", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convos = db.scalars(
        select(Conversation)
        .where(Conversation.owner_id == user.id)
        .order_by(Conversation.created_at.desc())
    ).all()
    return list(convos)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    convo = db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.owner_id == user.id)
        .options(selectinload(Conversation.messages))
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return convo


@router.post("/ask", response_model=AnswerResponse)
@limiter.limit("30/minute")
def ask(
    request: Request,
    payload: AskRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    blocked, reason = flag_question(payload.question)
    if blocked:
        # Persist the refusal so the conversation history is honest.
        convo = _get_or_create_conversation(db, user, payload.conversation_id, payload.document_id)
        db.add(
            Message(conversation_id=convo.id, role="user", content=payload.question, citations="[]")
        )
        db.add(
            Message(
                conversation_id=convo.id,
                role="assistant",
                content="I can't help with that request.",
                citations="[]",
            )
        )
        db.commit()
        db.refresh(convo)
        return AnswerResponse(
            conversation_id=convo.id,
            question=payload.question,
            answer="I can't help with that request.",
            citations=[],
            grounded=False,
            blocked=True,
            block_reason=reason,
        )

    if payload.document_id:
        doc = _get_owned_document(db, payload.document_id, user)
        source = doc.content
    elif payload.conversation_id:
        convo = db.scalar(
            select(Conversation)
            .where(Conversation.id == payload.conversation_id, Conversation.owner_id == user.id)
            .options(selectinload(Conversation.messages))
        )
        if not convo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
        source = "\n\n".join(m.content for m in convo.messages if m.role == "user")
        doc = None
    else:
        raise HTTPException(status_code=422, detail="Provide document_id or conversation_id")

    answer_text, citations, grounded = retrieve_answer(payload.question, source)

    convo = _get_or_create_conversation(db, user, payload.conversation_id, payload.document_id)
    db.add(Message(conversation_id=convo.id, role="user", content=payload.question, citations="[]"))
    db.add(
        Message(
            conversation_id=convo.id,
            role="assistant",
            content=answer_text,
            citations=json.dumps(citations),
        )
    )
    db.commit()
    db.refresh(convo)

    return AnswerResponse(
        conversation_id=convo.id,
        question=payload.question,
        answer=answer_text,
        citations=[Citation(snippet=c) for c in citations],
        grounded=grounded,
    )


def _get_or_create_conversation(
    db: Session, user: User, conversation_id: str | None, document_id: str | None
) -> Conversation:
    if conversation_id:
        convo = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.owner_id == user.id
            )
        )
        if not convo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
        return convo
    title = "New conversation"
    if document_id:
        doc = db.get(Document, document_id)
        if doc:
            title = doc.title[:60]
    convo = Conversation(owner_id=user.id, document_id=document_id, title=title)
    db.add(convo)
    db.flush()
    return convo
