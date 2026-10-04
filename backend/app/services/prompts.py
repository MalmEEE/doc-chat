from app.services.vector_store import RetrievedChunk

PROMPT_VERSION = "v2"
NOT_FOUND = "NOT_FOUND"

SYSTEM_PROMPT = """You are a study assistant that answers questions using ONLY the numbered
context passages provided. Rules:
1. Use only information from the context. Do not use outside knowledge.
2. After each sentence that uses a passage, cite it like [1] or [2][3].
3. The context may use different wording than the question (e.g. "results",
   "error", or "baseline" for a question about evaluation). Answer if any passage
   is relevant. Reply with exactly NOT_FOUND only if no passage is related to the
   question at all.
4. If the context only partly answers the question, answer that part, cite it,
   and say what is missing.
5. Be concise and clear. Use the student's wording where helpful."""


def build_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    history: list[tuple[str, str]] | None = None,
) -> str:
    """Build the user prompt: optional history, numbered context, then the question."""
    parts = []

    if history:
        lines = [
            f"{'User' if role == 'user' else 'Assistant'}: {content}"
            for role, content in history
        ]
        parts.append(
            "CONVERSATION SO FAR (for resolving follow-up questions only; "
            "not a source of facts):\n" + "\n".join(lines)
        )

    context = "\n\n".join(
        f"[{number}] ({chunk.filename}, page {chunk.page}) {chunk.text}"
        for number, chunk in enumerate(chunks, start=1)
    )
    parts.append(f"CONTEXT:\n{context}")
    parts.append(f"QUESTION:\n{question}")
    return "\n\n".join(parts)