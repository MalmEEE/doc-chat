# Project Charter - DocChat (working title)

| | |
|---|---|
| **Project** | DocChat - chat with your documents (RAG application) |
| **Owner / Developer** | Malmi Wimalaweera |
| **Status** | Phase 0 - Inception |
| **Last updated** | 2026-09-28 |

---

## 1. Problem statement

Students revise from large volumes of lecture slides, notes and research papers stored as PDFs. Finding a specific explanation, definition or fact means scrolling or keyword-searching through many files, and keyword search fails when the student doesn't know the exact wording used in the document.

General-purpose AI chatbots can answer questions, but their answers are not grounded in the student's own course material. They may contradict the lecturer's content or invent facts, and they don't show where an answer came from.

## 2. Vision

A web application where a student uploads their study PDFs and asks questions in natural language. They receive answers drawn **only** from their own documents, with citations to the source document and page, so every answer can be verified.

## 3. Target users

- **Primary:** university students revising from lecture notes, slides and papers.
- **Secondary:** anyone who needs to query a personal collection of text-based PDFs (e.g. researchers, professionals reading documentation).

## 4. Goals (v1)

1. Upload one or more text-based PDFs and have them processed automatically.
2. Ask natural-language questions across all uploaded documents, with the option to filter to a single document.
3. Receive answers generated only from retrieved document content, with citations (document name + page number).
4. Respond "I don't know / not found in your documents" when the answer isn't in the uploaded material.
5. Keep uploaded documents available after the server restarts.
6. Measure answer quality with a documented evaluation set, not just manual testing.

## 5. Non-goals (v1)

These are deliberately out of scope to protect the timeline:

- User accounts, login or multi-user support
- Scanned / image-only PDFs (OCR)
- File types other than PDF (.txt / .docx are candidates for a later version)
- Running the LLM locally (possible future "privacy mode")
- Mobile app
- Editing or annotating documents
- Production-grade scaling or security hardening

## 6. Scope summary

| In scope (v1) | Out of scope (v1) |
|---|---|
| PDF upload and ingestion pipeline | OCR for scanned PDFs |
| Local embeddings + vector search | Local LLM |
| Grounded Q&A with page citations | Authentication |
| Search across all docs / filter to one | Non-PDF formats |
| Persistent document store | Deployment at scale |
| Follow-up questions (Should-have) | |
| Evaluation set + results | |
| React web UI | |

## 7. Success criteria

Targets to validate after the technical spike; they may be revised with justification.

| # | Criterion | Target |
|---|---|---|
| SC-1 | Retrieval accuracy: correct source chunk appears in top-k results on the evaluation set | ≥ 80% of questions |
| SC-2 | Answer correctness on the evaluation set (manually graded) | ≥ 75% of questions |
| SC-3 | Every answer includes at least one citation (document + page) | 100% |
| SC-4 | Out-of-scope questions answered with "not found" rather than an invented answer | ≥ 80% of out-of-scope test questions |
| SC-5 | Typical answer time on the development laptop | under ~10 seconds |
| SC-6 | Project documented: README, design doc, ADRs, evaluation report | Complete at release |

## 8. Constraints

- **Hardware:** development laptop with 8 GB RAM, Intel i5-8265U (4-core laptop CPU), no dedicated GPU, ~44 GB free disk.
- **Cost:** zero budget; only free tiers and open-source tools.
- **Team:** single developer.
- **Time:** see Section 12 (to be confirmed).

## 9. Assumptions

- A hosted LLM API with a usable free tier (Gemini) is available without card details. *To be verified before design is finalised.*
- Test documents are text-based PDFs, not scans.
- A small local embedding model runs acceptably on the development laptop's CPU.

## 10. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM free-tier terms, limits or availability change | Medium | High | Isolate the LLM behind a provider interface so it can be swapped (another API or local Ollama) |
| LLM invents answers not in the documents (hallucination) | Medium | High | Strict grounding prompt, "not found" behaviour, citations, evaluation set |
| Limited RAM slows development | Medium | Medium | Local embeddings only; hosted LLM; small models |
| Poor text extraction from some PDFs (tables, columns) | Medium | Medium | Test with varied PDFs in the spike; document known limitations |
| Tooling issues on a preview Windows build | Low | Medium | Note issues early; fall back to alternative installers or versions |
| Scope creep | Medium | Medium | MoSCoW prioritisation; non-goals list; changes recorded in ADRs |

## 11. Tech stack (tentative — each confirmed via an ADR)

- **Frontend:** React
- **Backend:** Python, FastAPI
- **PDF parsing:** pypdf
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2), local
- **Vector store:** ChromaDB, persisted to disk
- **LLM:** Google Gemini API (free tier), behind a swappable provider interface
- **Testing:** pytest, FastAPI TestClient
- **Project management:** GitHub Issues + GitHub Projects

## 12. Milestones (draft — timeline to be confirmed)

| Milestone | Deliverable |
|---|---|
| M0 — Inception & requirements | Charter, requirements doc |
| M1 — Design & spike | Design doc, ADRs, wireframes, ingestion spike |
| M2 — Ingestion pipeline | Upload → extract → chunk → embed → store, with tests |
| M3 — Q&A API | Retrieval, grounded answers, citations, API endpoints |
| M4 — Frontend | React UI: upload, document list, chat with citations |
| M5 — Evaluation & release | Evaluation report, README, deployment, retrospective |