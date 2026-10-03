import os

from fastapi import APIRouter, Depends, File, Response, UploadFile

from app.config import Settings, get_settings
from app.errors import AppError
from app.schemas import DocumentListOut, DocumentOut
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

@router.get("", response_model=DocumentListOut)
def list_documents(repo: DocumentsRepo = Depends(get_documents_repo)):
    return DocumentListOut(
        documents=[DocumentOut.model_validate(d) for d in repo.list()]
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    store: VectorStore = Depends(get_vector_store),
    repo: DocumentsRepo = Depends(get_documents_repo),
):
    document = repo.get(document_id)
    if document is None:
        raise AppError(404, "DOCUMENT_NOT_FOUND", "Document not found.")

    store.delete_document(document_id)
    if os.path.exists(document.stored_path):
        os.remove(document.stored_path)
    repo.delete(document_id)
    return Response(status_code=204)