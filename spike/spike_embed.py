import time
import chromadb
from sentence_transformers import SentenceTransformer
from spike_ingest import extract_pages, chunk_pages, PDF_PATH, CHUNK_SIZE, CHUNK_OVERLAP

QUESTIONS = [
    "What problem does SmartTeaAI solve?",
    "Which models were used for forecasting?",
    "How was the model evaluated?",
]

# 1. Chunk the PDF
chunks = chunk_pages(extract_pages(PDF_PATH), CHUNK_SIZE, CHUNK_OVERLAP)

# 2. Load the embedding model (first run downloads ~90 MB)
t0 = time.perf_counter()
model = SentenceTransformer("all-MiniLM-L6-v2")
t1 = time.perf_counter()

# 3. Embed all chunks
texts = [c["text"] for c in chunks]
embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
t2 = time.perf_counter()

# 4. Store in Chroma (persisted to a folder on disk)
client = chromadb.PersistentClient(path="chroma_spike")
try:
    client.delete_collection("chunks")   # start fresh on each spike run
except Exception:
    pass
collection = client.create_collection("chunks", metadata={"hnsw:space": "cosine"})
collection.add(
    ids=[c["id"] for c in chunks],
    documents=texts,
    embeddings=embeddings.tolist(),
    metadatas=[{"page": c["page"]} for c in chunks],
)
t3 = time.perf_counter()

print(f"Chunks: {len(chunks)} | Embedding dimension: {embeddings.shape[1]}")
print(f"Model load: {t1 - t0:.2f}s | Embedding: {t2 - t1:.2f}s | Storing: {t3 - t2:.2f}s")

# 5. Search
for q in QUESTIONS:
    q_emb = model.encode([q], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=3)
    print(f"\n=== {q}")
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        print(f"  page {meta['page']:>2} | distance {dist:.3f} | {doc[:100]}...")