import time
from pypdf import PdfReader

PDF_PATH = "data/st20286196_CIS6035_PRES1.pdf"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def extract_pages(pdf_path):
    """Return a list of {"page": n, "text": ...}, 1-based page numbers, skipping empty pages."""
    reader = PdfReader(pdf_path)
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):  # start=1 → human page numbers
        text = page.extract_text() or ""   # extract_text() can return None
        text = " ".join(text.split())      # collapse messy line breaks and spaces
        if text:                           # skip empty (or image-only) pages
            pages.append({"page": page_num, "text": text})
    return pages

def chunk_pages(pages, size, overlap):
    """Split each page's text into overlapping chunks. Chunks never cross pages."""
    chunks = []
    step = size - overlap
    for p in pages:
        text = p["text"]
        start = 0
        index = 0
        while start < len(text):
            chunks.append({
                "id": f"{p['page']}:{index}",
                "page": p["page"],
                "text": text[start:start + size],
            })
            start += step
            index += 1
    return chunks

if __name__ == "__main__":
    t0 = time.perf_counter()
    pages = extract_pages(PDF_PATH)
    t1 = time.perf_counter()
    chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
    t2 = time.perf_counter()

    print(f"Pages with text: {len(pages)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Extraction: {t1 - t0:.2f}s | Chunking: {t2 - t1:.3f}s")
    if not chunks:
        print("No extractable text found — the PDF may be scanned.")
    else:
        print("\n--- Sample chunk ---")
        print(chunks[0])