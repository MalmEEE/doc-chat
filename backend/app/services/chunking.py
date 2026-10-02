from dataclasses import dataclass

from app.services.pdf_extract import PageText


@dataclass(frozen=True)
class Chunk:
    page: int    # page the chunk came from (for citations)
    index: int   # position of the chunk within its page, starting at 0
    text: str


def chunk_pages(pages: list[PageText], size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Split each page into overlapping chunks that end at word boundaries (ADR-004)."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("overlap must be 0 or more and smaller than size")

    chunks = []
    for p in pages:
        text = p.text
        start = 0
        index = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                # Prefer to end at the last space, but only one beyond the overlap zone.
                space = text.rfind(" ", start + overlap + 1, end)
                if space != -1:
                    end = space
            piece = text[start:end].strip()
            if piece:
                chunks.append(Chunk(page=p.page, index=index, text=piece))
                index += 1
            if end >= len(text):   # reached the end of the page
                break
            start = end - overlap  # step back so neighbouring chunks share context
    return chunks