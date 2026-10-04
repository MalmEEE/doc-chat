import os

from app.services.documents_repo import DocumentsRepo
from app.services.vector_store import VectorStore

LONG_TEXT = "Photosynthesis converts light energy into chemical energy stored in glucose."


def upload(client, path, name="notes.pdf"):
    with open(path, "rb") as f:
        return client.post("/api/documents", files={"file": (name, f, "application/pdf")})


def test_upload_valid_pdf_returns_201_and_summary(client, make_pdf):
    response = upload(client, make_pdf([LONG_TEXT, LONG_TEXT]))

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "notes.pdf"
    assert body["pages"] == 2
    assert body["chunks"] == 2
    assert "stored_path" not in body


def test_upload_non_pdf_is_rejected(client):
    response = client.post(
        "/api/documents", files={"file": ("notes.txt", b"hello", "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_upload_text_file_renamed_to_pdf_is_rejected(client):
    response = client.post(
        "/api/documents", files={"file": ("fake.pdf", b"just some text", "application/pdf")}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_upload_pdf_without_text_is_rejected_and_cleaned_up(client, make_pdf, tmp_path):
    response = upload(client, make_pdf(["", ""]))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_EXTRACTABLE_TEXT"
    assert client.get("/api/documents").json() == {"documents": []}
    assert os.listdir(tmp_path / "uploads") == []


def test_upload_too_large_is_rejected(client):
    too_big = b"%PDF-" + b"0" * (1024 * 1024 + 1)

    response = client.post(
        "/api/documents", files={"file": ("big.pdf", too_big, "application/pdf")}
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_list_shows_uploaded_documents(client, make_pdf):
    uploaded = upload(client, make_pdf([LONG_TEXT])).json()

    documents = client.get("/api/documents").json()["documents"]

    assert [d["id"] for d in documents] == [uploaded["id"]]


def test_delete_removes_document_then_returns_404(client, make_pdf):
    document_id = upload(client, make_pdf([LONG_TEXT])).json()["id"]

    assert client.delete(f"/api/documents/{document_id}").status_code == 204
    assert client.get("/api/documents").json() == {"documents": []}

    second = client.delete(f"/api/documents/{document_id}")
    assert second.status_code == 404
    assert second.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_uploaded_data_survives_a_restart(client, make_pdf, tmp_path):
    upload(client, make_pdf([LONG_TEXT, LONG_TEXT]))

    # Reopening the stores from disk is what a server restart does.
    assert len(DocumentsRepo(str(tmp_path / "test.db")).list()) == 1
    assert VectorStore(str(tmp_path / "chroma")).count() == 2