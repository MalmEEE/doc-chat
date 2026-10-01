import os
import re
import time

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

load_dotenv()
LLM_MODEL = os.environ["LLM_MODEL"]
TOP_K = 8

SYSTEM = """You are a study assistant that answers questions using ONLY the numbered
context passages provided. Rules:
1. Use only information from the context. Do not use outside knowledge.
2. After each sentence that uses a passage, cite it like [1] or [2][3].
3. The context may use different wording than the question (e.g. "results",
   "error", or "baseline" for a question about evaluation). Answer if any passage
   is relevant. Reply with exactly NOT_FOUND only if no passage is related to the
   question at all.
4. If the context only partly answers the question, answer that part, cite it,
   and say what is missing.
5. Be concise and clear."""

QUESTIONS = [
    "What problem does SmartTeaAI solve?",
    "Which models were used for forecasting?",
    "How was the model evaluated?",
    "What is the capital of France?",        # should be NOT_FOUND
    "Who won the 2022 FIFA World Cup?",      # should be NOT_FOUND
]

embedder = SentenceTransformer("all-MiniLM-L6-v2")
collection = chromadb.PersistentClient(path="chroma_spike").get_collection("chunks")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def build_prompt(question, docs, metas):
    context = "\n\n".join(
        f"[{i}] (page {m['page']}) {d}"
        for i, (d, m) in enumerate(zip(docs, metas), start=1)
    )
    return f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"


for q in QUESTIONS:
    t0 = time.perf_counter()
    q_emb = embedder.encode([q], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=TOP_K)
    docs, metas = res["documents"][0], res["metadatas"][0]
    
    t1 = time.perf_counter()

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=build_prompt(q, docs, metas),
        config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.2),
    )
    answer = (response.text or "").strip()
    t2 = time.perf_counter()

    print(f"\n=== {q}")
    print(f"  Retrieved pages: {[m['page'] for m in metas]}")
    if answer.startswith("NOT_FOUND"):
        print("  -> Not found in your documents.")
    else:
        print(f"  {answer}")
        refs = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer)})
        cited = [f"[{r}] page {metas[r - 1]['page']}" for r in refs if 1 <= r <= len(metas)]
        print(f"  Citations: {', '.join(cited) if cited else 'NONE (model did not cite)'}")
    print(f"  Retrieval: {t1 - t0:.2f}s | LLM: {t2 - t1:.2f}s | Total: {t2 - t0:.2f}s")

    time.sleep(4)  # stay under the free tier's 15 requests/minute