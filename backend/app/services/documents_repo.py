import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache

from app.config import get_settings


@dataclass(frozen=True)
class Document:
    id: str
    filename: str
    stored_path: str
    pages: int
    chunks: int
    uploaded_at: str   # ISO 8601, UTC


class DocumentsRepo:
    """Source of truth for the document list (design §5)."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        folder = os.path.dirname(db_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id          TEXT PRIMARY KEY,
                    filename    TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    pages       INTEGER NOT NULL,
                    chunks      INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add(self, doc: Document) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO documents (id, filename, stored_path, pages, chunks, uploaded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (doc.id, doc.filename, doc.stored_path, doc.pages, doc.chunks, doc.uploaded_at),
            )

    def list(self) -> list[Document]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
        return [Document(**dict(row)) for row in rows]

    def get(self, document_id: str) -> Document | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return Document(**dict(row)) if row else None

    def delete(self, document_id: str) -> bool:
        """Return True if a document was deleted, False if it didn't exist."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return cursor.rowcount > 0


@lru_cache
def get_documents_repo() -> DocumentsRepo:
    return DocumentsRepo(os.path.join(get_settings().data_dir, "docchat.db"))