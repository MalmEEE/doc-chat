import pytest
from fpdf import FPDF
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.services.documents_repo import DocumentsRepo, get_documents_repo
from app.services.vector_store import VectorStore, get_vector_store
from app.llm.fake import FakeProvider
from app.llm.gemini import get_llm_provider


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

@pytest.fixture
def fake_llm():
    return FakeProvider("Photosynthesis makes glucose. [1]")


@pytest.fixture
def client(tmp_path, fake_llm):
    """A test client whose data lives in a temporary folder, not backend/data."""
    settings = Settings(data_dir=str(tmp_path), max_upload_mb=1)
    store = VectorStore(str(tmp_path / "chroma"))
    repo = DocumentsRepo(str(tmp_path / "test.db"))

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_vector_store] = lambda: store
    app.dependency_overrides[get_documents_repo] = lambda: repo
    app.dependency_overrides[get_llm_provider] = lambda: fake_llm
    yield TestClient(app)
    app.dependency_overrides.clear()