import pytest

from app.services.chunking import chunk_pages
from app.services.pdf_extract import PageText


def words_text(n):
    """n distinct 5-letter words separated by spaces: 'w0000 w0001 ...'"""
    return " ".join(f"w{i:04d}" for i in range(n))


LONG = words_text(334)   # 2,003 characters


def test_empty_input_gives_no_chunks():
    assert chunk_pages([]) == []


def test_short_page_becomes_one_chunk():
    chunks = chunk_pages([PageText(page=5, text="A short slide.")])

    assert len(chunks) == 1
    assert chunks[0].page == 5
    assert chunks[0].index == 0
    assert chunks[0].text == "A short slide."


def test_page_of_exactly_chunk_size_becomes_one_chunk():
    chunks = chunk_pages([PageText(page=1, text="x" * 800)])

    assert len(chunks) == 1


def test_chunks_never_exceed_size():
    chunks = chunk_pages([PageText(page=1, text=LONG)])

    assert all(len(c.text) <= 800 for c in chunks)


def test_chunks_end_at_word_boundaries():
    chunks = chunk_pages([PageText(page=1, text=LONG)])

    for c in chunks:
        end = LONG.find(c.text) + len(c.text)
        assert end == len(LONG) or LONG[end] == " "


def test_consecutive_chunks_overlap():
    chunks = chunk_pages([PageText(page=1, text=LONG)])

    assert chunks[1].text[:50] in chunks[0].text


def test_chunk_count_is_sane():
    """Regression test for the spike bug that produced thousands of chunks."""
    chunks = chunk_pages([PageText(page=1, text=LONG)])

    assert 2 <= len(chunks) <= 4


def test_text_without_spaces_is_still_chunked():
    chunks = chunk_pages([PageText(page=1, text="x" * 2000)])

    assert 2 <= len(chunks) <= 4
    assert all(len(c.text) <= 800 for c in chunks)

def test_chunks_keep_page_numbers_and_index_restarts():
    pages = [
        PageText(page=3, text="First short page."),
        PageText(page=7, text="Second short page."),
    ]

    chunks = chunk_pages(pages)

    assert [c.page for c in chunks] == [3, 7]
    assert [c.index for c in chunks] == [0, 0]


def test_overlap_not_smaller_than_size_raises():
    with pytest.raises(ValueError):
        chunk_pages([PageText(page=1, text="some text")], size=100, overlap=100)