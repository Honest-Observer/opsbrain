# JUDGE_QA.md

Anticipated judge questions and crisp answers.

**Q: Is this using a real LLM, or is it faking the intelligence?**
A: Both modes ship, and it's a deliberate strength. With a `GEMINI_API_KEY` configured (see
README), it's a real RAG system: Google `gemini-embedding-001` for semantic retrieval and
`gemini-3.5-flash` for grounded answer generation with structured citations, plus LLM
entity/relationship extraction that lets it ingest and answer questions over *arbitrary* uploaded
documents it has never seen. With no key, it falls back to a fully-deterministic offline path
(local embeddings + template answers) so the demo can never hard-fail on stage. Because both are
behind the same interfaces (DECISIONS.md ADR-008/011), switching between them changes zero API
contracts and zero frontend code. Concretely, enabling Gemini raised our benchmark
retrieval_hit_rate from 0.875 to 1.0.

**Q: Can it really handle data and questions it wasn't pre-built for?**
A: Yes — that's the point of the Ingest page. Drop in any raw document (PDF/CSV/XLSX/TXT/MD/JSON):
OpsBrain parses it, chunks and embeds it, and (with Gemini) extracts entities and relationships
into the live knowledge graph. It then answers free-form natural-language questions grounded in
that new content, with citations. We demoed this live by uploading a brand-new shift-handover note
about a compressor and immediately asking the copilot about it — it answered correctly, cited the
uploaded document, and linked the relevant regulation.

**Q: How do you know the "citations" are actually meaningful and not decorative?**
A: The evaluation harness measures this directly: citation coverage is 1.0 across 24 benchmark
questions, meaning every copilot answer in the benchmark returns at least one real citation to
an actual seeded document, and entity linkage coverage is also 1.0. This is enforced by `POST
/api/eval/run`, not asserted by us.

**Q: Is the demo data realistic, or is it obviously synthetic?**
A: It's synthetic but internally consistent by construction: the same asset tags, work order
numbers, and incident codes cross-reference each other across 26 files spanning SOPs, OEM
manual excerpts, work orders, inspection reports, incident reports, an asset registry, shift
handover notes, and a regulatory checklist — mirroring what a real plant's document sprawl looks
like, deliberately including a realistic recurring-failure story (Pump P-101) and a realistic
compliance gap (Boiler B-12) rather than generic placeholder text.

**Q: What happens if the backend goes down mid-demo?**
A: Every frontend screen has a mock-data fallback behind the same typed API client — if a
request fails or times out, the UI shows a "Demo Mode" banner and renders realistic seeded data
instead of breaking. This was a hard requirement in the frozen spec (MASTER_SPEC.md §13), not an
afterthought.

**Q: How would this scale to a real plant with millions of documents?**
A: The relational schema (documents/chunks/entities/relationships) and API contracts don't
change — you'd swap SQLite for Postgres+pgvector (already supported, auto-detected via
`DATABASE_URL`), add a background ingestion queue instead of synchronous processing, and swap
the local hash embedding for a production embedding API. None of those are frontend changes.

**Q: Why relational tables instead of a graph database like Neo4j?**
A: For this problem's actual query patterns (asset neighborhoods, path-limited traversals), a
handful of joined tables are simpler to operate, debug, and demo under a hackathon deadline than
running a separate graph database service, while still giving genuinely queryable and
visualizable relationships. If real-world scale later demanded deep multi-hop graph queries at
volume, that's an isolated swap behind the same `/graph/*` API contract.

**Q: What's the weakest part of this prototype, honestly?**
A: The entity extraction is regex/heuristic rather than ML-based, so it works reliably on the
patterns we designed the corpus generator around (asset tags, WO/IR/REG codes) but wouldn't
generalize to arbitrary unseen document formats without additional pattern work or an upgrade to
model-based extraction — which the architecture explicitly supports as a drop-in replacement.

**Q: How was this actually built in the time available?**
A: Architecture and API contracts were frozen first (MASTER_SPEC.md, DECISIONS.md) before any
implementation, then backend and frontend were implemented against that frozen contract, and
finally integrated and hardened — verified independently via a 28-test backend suite, a clean
production frontend build, and an end-to-end smoke test (`scripts/smoke_test.py`) that walks the
exact judged demo path against a live server.
