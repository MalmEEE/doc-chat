import logging
import re
from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.services.embeddings import embed_texts
from app.services.prompts import NOT_FOUND, SYSTEM_PROMPT, build_prompt
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

NO_DOCUMENTS_MESSAGE = "Upload a document first."
NOT_FOUND_MESSAGE = "I couldn't find this in your documents."
SNIPPET_CHARS = 300


@dataclass(frozen=True)
class Citation:
    ref: int          # the [n] number used in the answer text
    document_id: str
    filename: str
    page: int
    snippet: str


@dataclass(frozen=True)
class Answer:
    answer: str
    found: bool
    citations: list[Citation]


def answer_question(
    *,
    question: str,
    store: VectorStore,
    llm: LLMProvider,
    top_k: int,
    document_id: str | None = None,
    embed=embed_texts,
) -> Answer:
    """Answer a question from the stored chunks, with citations (design §3)."""
    if store.count() == 0:
        return Answer(answer=NO_DOCUMENTS_MESSAGE, found=False, citations=[])

    chunks = store.query(embed([question])[0], top_k, document_id)
    if not chunks:
        return Answer(answer=NOT_FOUND_MESSAGE, found=False, citations=[])

    raw = llm.generate(SYSTEM_PROMPT, build_prompt(question, chunks)).strip()
    if not raw or raw.upper().startswith(NOT_FOUND):
        return Answer(answer=NOT_FOUND_MESSAGE, found=False, citations=[])

    refs: list[int] = []
    for match in re.findall(r"\[(\d+)\]", raw):
        ref = int(match)
        if 1 <= ref <= len(chunks) and ref not in refs:
            refs.append(ref)
    if not refs:
        logger.warning("Answer had no citations; citing the top retrieved chunk")
        refs = [1]

    citations = [
        Citation(
            ref=ref,
            document_id=chunks[ref - 1].document_id,
            filename=chunks[ref - 1].filename,
            page=chunks[ref - 1].page,
            snippet=chunks[ref - 1].text[:SNIPPET_CHARS],
        )
        for ref in refs
    ]
    return Answer(answer=raw, found=True, citations=citations)