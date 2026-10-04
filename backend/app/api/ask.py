from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.errors import AppError
from app.llm.base import LLMError, LLMProvider, LLMRateLimitError
from app.llm.gemini import get_llm_provider
from app.schemas import AskRequest, AskResponse, CitationOut
from app.services.documents_repo import DocumentsRepo, get_documents_repo
from app.services.rag import answer_question
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(prefix="/api", tags=["ask"])

MAX_QUESTION_CHARS = 1000


@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    settings: Settings = Depends(get_settings),
    store: VectorStore = Depends(get_vector_store),
    repo: DocumentsRepo = Depends(get_documents_repo),
    llm: LLMProvider = Depends(get_llm_provider),
):
    question = body.question.strip()
    if not question:
        raise AppError(400, "EMPTY_QUESTION", "Please enter a question.")
    if len(question) > MAX_QUESTION_CHARS:
        raise AppError(400, "QUESTION_TOO_LONG", "Questions must be under 1,000 characters.")
    if body.document_id and repo.get(body.document_id) is None:
        raise AppError(404, "DOCUMENT_NOT_FOUND", "Document not found.")

    try:
        result = answer_question(
            question=question,
            store=store,
            llm=llm,
            top_k=settings.top_k,
            document_id=body.document_id,
            history=[(m.role, m.content) for m in body.history],
        )
    except LLMRateLimitError as exc:
        raise AppError(429, "RATE_LIMITED",
                       "Too many questions right now. Please try again shortly.",
                       retry_after_seconds=exc.retry_after_seconds)
    except LLMError:
        raise AppError(502, "LLM_ERROR", "The answer service is unavailable. Please try again.")

    return AskResponse(
        answer=result.answer,
        found=result.found,
        citations=[CitationOut.model_validate(c) for c in result.citations],
    )