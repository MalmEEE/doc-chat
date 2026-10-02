import pytest

from app.services.pdf_extract import NoExtractableTextError, clean_text, extract_pages

LONG_TEXT = "Photosynthesis converts light energy into chemical energy stored in glucose."


def test_clean_text_collapses_whitespace():
    assert clean_text("  hello \n\n  world\t again ") == "hello world again"


def test_clean_text_handles_none():
    assert clean_text(None) == ""


def test_extract_pages_returns_text_with_page_numbers(make_pdf):
    path = make_pdf([LONG_TEXT, "Second page talks about cellular respiration."])

    pages = extract_pages(path)

    assert [p.page for p in pages] == [1, 2]
    assert "Photosynthesis" in pages[0].text
    assert "respiration" in pages[1].text

def test_extract_pages_skips_blank_pages_but_keeps_numbering(make_pdf):
    path = make_pdf([LONG_TEXT, "", LONG_TEXT])

    pages = extract_pages(path)

    assert [p.page for p in pages] == [1, 3]

def test_extract_pages_raises_for_pdf_without_text(make_pdf):
    path = make_pdf(["", ""])

    with pytest.raises(NoExtractableTextError):
        extract_pages(path)