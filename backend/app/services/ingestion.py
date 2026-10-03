import os
import uuid
from datetime import datetime, timezone

from pypdf.errors import PyPdfError

from app.config import Settings
from app.errors import AppError
from app.services.chunking import chunk_pages
from app.services.documents_repo import Document, DocumentsRepo
from app.services.embeddings import embed_texts
from app.services.pdf_extract import NoExtractableTextError, extract_pages
from app.services.vector_store import VectorStore


def ingest_pdf(
    *,
    filename: str,
    content: bytes,
    settings: Settings,
    store: VectorStore,
    repo: DocumentsRepo,
    embed=embed_texts,
) -> Document:
    """Save, extract, chunk, embed and store one PDF. Cleans up if anything fails."""
    document_id = uuid.uuid4().hex
    uploads_dir = os.path.join(settings.data_dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    stored_path = os.path.join(uploads_dir, f"{document_id}.pdf")

    with open(stored_path, "wb") as f:
        f.write(content)

    try:
        try:
            pages = extract_pages(stored_path)
        except NoExtractableTextError:
            raise AppError(422, "NO_EXTRACTABLE_TEXT",
                           "This PDF has no selectable text (it may be a scan).")
        except PyPdfError:
            raise AppError(400, "INVALID_FILE_TYPE", "This file could not be read as a PDF.")

        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        vectors = embed([c.text for c in chunks])
        store.add(document_id, filename, chunks, vectors)

        document = Document(
            id=document_id,
            filename=filename,
            stored_path=stored_path,
            pages=len(pages),
            chunks=len(chunks),
            uploaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        )
        repo.add(document)
        return document
    except Exception as exc:
        # Leave nothing half-ingested behind (design §2).
        store.delete_document(document_id)
        if os.path.exists(stored_path):
            os.remove(stored_path)
        if isinstance(exc, AppError):
            raise
        raise AppError(500, "INGESTION_FAILED", "The document could not be processed.") from exc