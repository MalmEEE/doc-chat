from typing import Literal

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    pages: int
    chunks: int
    uploaded_at: str


class DocumentListOut(BaseModel):
    documents: list[DocumentOut]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    question: str
    document_id: str | None = None
    history: list[ChatMessage] = []


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ref: int
    document_id: str
    filename: str
    page: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    found: bool
    citations: list[CitationOut]