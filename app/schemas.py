"""Pydantic request/response schemas."""

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=120)

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("a valid email address is required")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    char_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentOut):
    content: str


class SummarizeRequest(BaseModel):
    document_id: str
    ratio: float = Field(default=0.3, ge=0.1, le=0.9)
    max_sentences: int = Field(default=8, ge=1, le=50)


class SummarizeResponse(BaseModel):
    document_id: str
    summary: str
    sentence_count: int
    compression_ratio: float
    grounded: bool = True


class AskRequest(BaseModel):
    conversation_id: str | None = None
    document_id: str | None = None
    question: str = Field(min_length=1, max_length=2000)


class Citation(BaseModel):
    snippet: str


class AnswerResponse(BaseModel):
    conversation_id: str
    question: str
    answer: str
    citations: list[Citation]
    grounded: bool
    blocked: bool = False
    block_reason: str | None = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_validator("citations", mode="before")
    @classmethod
    def _parse_citations(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return []
        return v or []


class ConversationOut(BaseModel):
    id: str
    title: str
    document_id: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
