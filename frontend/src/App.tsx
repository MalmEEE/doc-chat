import { useEffect, useState } from "react";
import { ApiError, listDocuments, type DocumentInfo } from "./api";

export default function App() {
  const [documents, setDocuments] = useState<DocumentInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((e: ApiError) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>DocChat</h1>
      {error && <p>{error}</p>}
      {documents && <p>Connected. {documents.length} document(s) uploaded.</p>}
      <ul>
        {documents?.map((d) => (
          <li key={d.id}>{d.filename} ({d.pages} pages)</li>
        ))}
      </ul>
    </main>
  );
}