from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings


@lru_cache
def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it for every request."""
    return SentenceTransformer(get_settings().embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one normalised vector per input text."""
    if not texts:
        return []
    vectors = get_model().encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return vectors.tolist()