const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type DocumentInfo = {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  uploaded_at: string;
};

export type Citation = {
  ref: number;
  document_id: string;
  filename: string;
  page: number;
  snippet: string;
};

export type AskResponse = {
  answer: string;
  found: boolean;
  citations: Citation[];
};

export type ChatTurn = { role: "user" | "assistant"; content: string };

export class ApiError extends Error {
  status: number;
  code: string;
  retryAfterSeconds?: number;

  constructor(status: number, code: string, message: string, retryAfterSeconds?: number) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Can't reach the server. Is the backend running?");
  }

  if (response.status === 204) return undefined as T;

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const error = body?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "UNKNOWN",
      error?.message ?? "Something went wrong.",
      error?.retry_after_seconds,
    );
  }
  return body as T;
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const body = await request<{ documents: DocumentInfo[] }>("/api/documents");
  return body.documents;
}

export function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  return request<DocumentInfo>("/api/documents", { method: "POST", body: form });
}

export function deleteDocument(id: string): Promise<void> {
  return request<void>(`/api/documents/${id}`, { method: "DELETE" });
}

export function askQuestion(
  question: string,
  documentId: string | null,
  history: ChatTurn[],
): Promise<AskResponse> {
  return request<AskResponse>("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId, history }),
  });
}