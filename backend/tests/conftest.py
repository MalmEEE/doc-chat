import pytest
from fpdf import FPDF


@pytest.fixture
def make_pdf(tmp_path):
    """Returns a function that builds a PDF with one page per string ("" = blank page)."""
    def _make(page_texts, name="test.pdf"):
        pdf = FPDF()
        for text in page_texts:
            pdf.add_page()
            if text:
                pdf.set_font("Helvetica", size=12)
                pdf.multi_cell(0, 8, text)
        path = tmp_path / name
        pdf.output(str(path))
        return path
    return _make