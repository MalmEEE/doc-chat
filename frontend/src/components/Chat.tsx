import { type FormEvent, useEffect, useRef, useState } from "react";
import { ApiError, askQuestion, type ChatTurn, type Citation } from "../api";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  found?: boolean;
  citations?: Citation[];
  isError?: boolean;
};

const HISTORY_MESSAGES = 6;

function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.code === "RATE_LIMITED" && e.retryAfterSeconds) {
      return `Too many questions right now. Try again in ${e.retryAfterSeconds} seconds.`;
    }
    return e.message;
  }
  return "Something went wrong.";
}

function Citations({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const selected = citations.find((c) => c.ref === open);

  return (
    <>
      <div className="citations">
        {citations.map((c) => (
          <button
            key={c.ref}
            className="chip"
            aria-expanded={open === c.ref}
            onClick={() => setOpen(open === c.ref ? null : c.ref)}
          >
            [{c.ref}] {c.filename} · p.{c.page}
          </button>
        ))}
      </div>
      {selected && <blockquote className="snippet">{selected.snippet}</blockquote>}
    </>
  );
}

type Props = { scope: string | null; hasDocuments: boolean };

export default function Chat({ scope, hasDocuments }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const nextId = useRef(1);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function add(message: Omit<Message, "id">) {
    const id = nextId.current++;
    setMessages((current) => [...current, { ...message, id }]);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    // The backend is stateless, so recent turns travel with each question.
    const history: ChatTurn[] = messages
      .filter((m) => !m.isError)
      .slice(-HISTORY_MESSAGES)
      .map(({ role, content }) => ({ role, content }));

    add({ role: "user", content: question });
    setInput("");
    setLoading(true);
    try {
      const result = await askQuestion(question, scope, history);
      add({
        role: "assistant",
        content: result.answer,
        found: result.found,
        citations: result.citations,
      });
    } catch (e) {
      add({ role: "assistant", content: errorText(e), isError: true });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="messages">
        {messages.length === 0 && (
          <p className="placeholder">
            {hasDocuments
              ? "Ask a question about your documents."
              : "Upload a PDF to get started."}
          </p>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={[
              "message",
              m.role,
              m.isError ? "failed" : "",
              m.found === false ? "not-found" : "",
            ].join(" ")}
          >
            {m.content}
            {m.citations && m.citations.length > 0 && <Citations citations={m.citations} />}
          </div>
        ))}

        {loading && <div className="message assistant not-found">Searching your documents…</div>}
        <div ref={bottom} />
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          className="field"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your documents"
          maxLength={1000}
          disabled={loading}
        />
        <button className="button" disabled={loading || !input.trim()}>
          Ask
        </button>
      </form>
    </>
  );
}