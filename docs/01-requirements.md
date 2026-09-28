# Requirements — DocChat

| | |
|---|---|
| **Phase** | 1 — Requirements |
| **Related** | [Project charter](00-project-charter.md) |
| **Last updated** | 2026-09-28 |

---

## 1. User stories

| ID | User story | Priority |
|---|---|---|
| US-1 | As a student, I want to upload a PDF of my lecture notes so that I can ask questions about it. | Must |
| US-2 | As a student, I want to see which documents I've uploaded so that I know what the app can answer from. | Must |
| US-3 | As a student, I want to ask a question in plain English and get an answer from my documents so that I don't have to search through them manually. | Must |
| US-4 | As a student, I want each answer to show the document and page it came from so that I can check it against the original. | Must |
| US-5 | As a student, I want the app to tell me when the answer isn't in my documents so that I'm not misled by an invented answer. | Must |
| US-6 | As a student, I want my uploaded documents to still be there when I come back so that I don't have to re-upload them. | Must |
| US-7 | As a student, I want to delete a document so that outdated notes don't affect my answers. | Should |
| US-8 | As a student, I want to limit a question to one document so that I get answers from a specific module or paper. | Should |
| US-9 | As a student, I want to ask follow-up questions so that I can dig deeper without repeating context. | Should |
| US-10 | As a student, I want to see the retrieved source text behind an answer so that I can read the surrounding context. | Could |
| US-11 | As a student, I want to upload .txt or .docx files so that I can use notes in other formats. | Won't (v1) |

**MoSCoW summary:** 6 Must, 3 Should, 1 Could, 1 Won't (v1). The Musts define the minimum releasable product.

---

## 2. Functional requirements

| ID | Requirement | Story | Priority |
|---|---|---|---|
| FR-1 | The system shall accept PDF uploads and reject other file types with a clear error. | US-1 | Must |
| FR-2 | The system shall extract text from each page, split it into overlapping chunks, embed the chunks, and store them with document ID, filename and page number. | US-1 | Must |
| FR-3 | The system shall detect PDFs with no extractable text (e.g. scans) and report that they can't be processed. | US-1 | Must |
| FR-4 | The system shall list uploaded documents with name, page count and upload date. | US-2 | Must |
| FR-5 | The system shall retrieve the top-k most relevant chunks for a question and generate an answer using only those chunks. | US-3 | Must |
| FR-6 | Every answer shall include citations (document name + page number) for the chunks used. | US-4 | Must |
| FR-7 | If the retrieved content does not contain the answer, the system shall respond that the answer was not found in the documents. | US-5 | Must |
| FR-8 | Documents and embeddings shall persist to disk and be available after a server restart. | US-6 | Must |
| FR-9 | The system shall allow deleting a document and all of its stored chunks. | US-7 | Should |
| FR-10 | The system shall allow restricting retrieval to a single selected document. | US-8 | Should |
| FR-11 | The system shall use recent conversation turns to interpret follow-up questions. | US-9 | Should |
| FR-12 | The system shall allow the user to expand a citation to view the source chunk text. | US-10 | Could |

---

## 3. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Performance | A typical question is answered within ~10 seconds on the development laptop (target; validated in the spike). |
| NFR-2 | Performance | A 50-page text PDF is ingested within ~1 minute on the development laptop (target; validated in the spike). |
| NFR-3 | Resource use | The backend runs within the development laptop's 8 GB RAM alongside the dev tools; no local LLM. |
| NFR-4 | Cost | The system uses only free tiers and open-source components. |
| NFR-5 | Grounding | Answers must not contain facts not supported by retrieved chunks; measured through the evaluation set (charter SC-2, SC-4). |
| NFR-6 | Maintainability | The LLM provider is isolated behind an interface so it can be replaced without changing the rest of the pipeline. |
| NFR-7 | Security | API keys are loaded from environment variables and never committed to the repository. |
| NFR-8 | Privacy | Document text is sent to the LLM provider only as retrieved chunks at question time, and this is stated in the README. |
| NFR-9 | Usability | Errors (bad file type, unreadable PDF, API failure, rate limit) are shown to the user in plain language. |
| NFR-10 | Testability | Core pipeline functions (extraction, chunking, retrieval, prompt building) have unit tests. |

---

## 4. Acceptance criteria (Must-haves)

**US-1 / FR-1–3 — Upload**
- Given a text-based PDF, when I upload it, then it appears in the document list and its content can be queried.
- Given a non-PDF file, when I upload it, then I see an error and nothing is stored.
- Given a scanned PDF with no extractable text, when I upload it, then I see a message that it can't be processed.

**US-2 / FR-4 — Document list**
- Given uploaded documents, when I open the app, then I see each document's name, page count and upload date.

**US-3 / FR-5 — Ask a question**
- Given at least one uploaded document, when I ask a question whose answer is in it, then I receive an answer based on that content.

**US-4 / FR-6 — Citations**
- Given any answer, then it shows at least one citation with the document name and page number.

**US-5 / FR-7 — Not found**
- Given a question unrelated to my documents, when I ask it, then the system says the answer isn't in my documents instead of answering from general knowledge.

**US-6 / FR-8 — Persistence**
- Given uploaded documents, when the backend restarts, then the documents are still listed and queryable.

---

## 5. Out of scope (v1)

See charter Section 5: authentication, OCR, non-PDF formats, local LLM, mobile app, scaling.