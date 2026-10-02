from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

MIN_TEXT_CHARS = 50


class NoExtractableTextError(Exception):
    """The PDF has no usable text, e.g. it is a scan (FR-3)."""


@dataclass(frozen=True)
class PageText:
    page: int   # 1-based page number, used for citations
    text: str


def clean_text(text: str | None) -> str:
    """Collapse line breaks and repeated spaces into single spaces."""
    return " ".join((text or "").split())


def extract_pages(pdf_path: str | Path) -> list[PageText]:
    """Return the text of each non-empty page, keeping original page numbers."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text())
        if text:
            pages.append(PageText(page=number, text=text))

    if sum(len(p.text) for p in pages) < MIN_TEXT_CHARS:
        raise NoExtractableTextError("This PDF has no extractable text.")
    return pages