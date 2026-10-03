import os
from dataclasses import dataclass
from functools import lru_cache

import chromadb

from app.config import get_settings
from app.services.chunking import Chunk

COLLECTION_NAME = "chunks"


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    filename: str
    page: int
    text: str
    distance: float   # cosine distance: lower means more similar


class VectorStore:
    """The only place in the app that talks to ChromaDB (ADR-002)."""

    def __init__(self, path: str):
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    def add(self, document_id: str, filename: str, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self._collection.add(
            ids=[f"{document_id}:{c.page}:{c.index}" for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[
                {"document_id": document_id, "filename": filename, "page": c.page, "chunk_index": c.index}
                for c in chunks
            ],
        )

    def query(self, embedding: list[float], top_k: int, document_id: str | None = None) -> list[RetrievedChunk]:
        total = self._collection.count()
        if total == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, total),
            where={"document_id": document_id} if document_id else None,
        )
        return [
            RetrievedChunk(
                document_id=meta["document_id"],
                filename=meta["filename"],
                page=meta["page"],
                text=text,
                distance=distance,
            )
            for text, meta, distance in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0]
            )
        ]

    def delete_document(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})

    def count(self) -> int:
        return self._collection.count()


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore(os.path.join(get_settings().data_dir, "chroma"))