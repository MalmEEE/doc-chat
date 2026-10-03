import os

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import Settings, get_settings
from app.errors import AppError
from app.schemas import DocumentOut
from app.services.documents_repo import DocumentsRepo, get_documents_repo
from app.services.ingestion import ingest_pdf
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    store: VectorStore = Depends(get_vector_store),
    repo: DocumentsRepo = Depends(get_documents_repo),
):
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".pdf"):
        raise AppError(400, "INVALID_FILE_TYPE", "Only PDF files are supported.")

    content = file.file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise AppError(413, "FILE_TOO_LARGE", f"Files must be under {settings.max_upload_mb} MB.")
    if not content.startswith(b"%PDF-"):
        raise AppError(400, "INVALID_FILE_TYPE", "Only PDF files are supported.")

    document = ingest_pdf(
        filename=filename, content=content, settings=settings, store=store, repo=repo
    )
    return DocumentOut.model_validate(document)