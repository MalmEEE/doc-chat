import { useCallback, useEffect, useState } from "react";
import { ApiError, listDocuments, type DocumentInfo } from "./api";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";

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
        {loadError && <p className="banner" role="alert">{loadError}</p>}
        <Chat scope={scope} hasDocuments={documents.length > 0} />
      </main>
    </div>
  );
}