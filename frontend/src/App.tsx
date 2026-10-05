import { useCallback, useEffect, useState } from "react";
import { ApiError, listDocuments, type DocumentInfo } from "./api";
import Sidebar from "./components/Sidebar";

export default function App() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [scope, setScope] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const reload = useCallback(() => {
    listDocuments()
      .then((docs) => { setDocuments(docs); setLoadError(null); })
      .catch((e: ApiError) => setLoadError(e.message));
  }, []);

  useEffect(reload, [reload]);

  return (
    <div className="app">
      <Sidebar documents={documents} scope={scope} onScopeChange={setScope} onChanged={reload} />
      <main className="chat">
        <p className="placeholder">{loadError ?? "Chat comes next."}</p>
      </main>
    </div>
  );
}