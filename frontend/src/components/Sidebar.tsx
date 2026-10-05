import { type ChangeEvent, useRef, useState } from "react";
import { ApiError, deleteDocument, uploadDocument, type DocumentInfo } from "../api";

type Props = {
  documents: DocumentInfo[];
  scope: string | null;                       // null = search all documents
  onScopeChange: (id: string | null) => void;
  onChanged: () => void;                      // ask the parent to reload the list
};

export default function Sidebar({ documents, scope, onScopeChange, onChanged }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";                  // lets the same file be picked again
    if (!file) return;

    setError(null);
    setUploading(true);
    try {
      await uploadDocument(file);
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(doc: DocumentInfo) {
    if (!window.confirm(`Delete "${doc.filename}"?`)) return;

    setError(null);
    try {
      await deleteDocument(doc.id);
      if (scope === doc.id) onScopeChange(null);
      onChanged();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Delete failed.");
    }
  }

  return (
    <aside className="sidebar">
    <h1 className="brand">
        <img src="/favicon.svg" alt="" width="28" height="28" />
        DocChat
      </h1>

      <input ref={fileInput} type="file" accept="application/pdf,.pdf" hidden onChange={handleFile} />
      <button className="button" disabled={uploading} onClick={() => fileInput.current?.click()}>
        {uploading ? "Processing…" : "Upload PDF"}
      </button>
      {error && <p className="error" role="alert">{error}</p>}

      <h2>Search in</h2>
      <select
        className="field"
        value={scope ?? ""}
        onChange={(e) => onScopeChange(e.target.value || null)}
      >
        <option value="">All documents</option>
        {documents.map((doc) => (
          <option key={doc.id} value={doc.id}>{doc.filename}</option>
        ))}
      </select>

      <h2>Documents</h2>
      {documents.length === 0 ? (
        <p className="notice">No documents yet. Upload a PDF to get started.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li key={doc.id} className="doc">
              <div>
                <div className="doc-name">{doc.filename}</div>
                <div className="doc-meta">
                  {doc.pages} pages · {new Date(doc.uploaded_at).toLocaleDateString()}
                </div>
              </div>
              <button className="doc-delete" aria-label={`Delete ${doc.filename}`} onClick={() => handleDelete(doc)}>
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}