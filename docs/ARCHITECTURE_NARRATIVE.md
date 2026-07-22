# ARCHITECTURE_NARRATIVE.md

Companion narrative to `docs/ARCHITECTURE_DIAGRAM.mmd` — read this alongside the diagram.

OpsBrain's architecture is a single pipeline with eight stages, each one independently real and
verifiable, not a stitched-together demo.

**1. Document ingestion.** The system accepts the heterogeneous format mix a real plant actually
produces — PDF manuals, Markdown SOPs, CSV asset registries, XLSX compliance checklists, JSON
work orders, plain-text handover notes, and simulated scanned inspection forms. Twenty-six such
files, cross-referencing the same asset tags and case numbers, make up the seeded demo corpus.

**2. Parsing and chunking.** Each format has a dedicated parser that normalizes it to
`(text, metadata)`. Text is then chunked to roughly 250–400 tokens with exact character offsets
retained, so every later citation can point back to a precise span of a real source document —
not just "somewhere in this PDF."

**3. Entity extraction.** A regex/heuristic layer — deliberately the primary extraction path,
not a fallback behind an unavailable LLM — pulls out asset tags, work order numbers, incident
codes, regulation references, dates, and personnel names. This is what turns unstructured text
into structured, linkable facts.

**4. Graph storage.** Extracted entities become graph nodes; eight relationship types (asset↔
document, asset↔work order, asset↔incident, incident↔regulation, asset↔procedure, work order↔
failure mode, inspection↔compliance gap, incident↔incident similarity) become edges — stored as
ordinary relational tables, not a separate graph database, so the whole system stays operable by
one person under a deadline while still supporting real graph queries.

**5. Vector / search layer.** Every chunk gets a deterministic local embedding (no network call,
no API key) and semantic search runs via cosine similarity — swappable later for a production
embedding provider or Postgres+pgvector without touching any caller code.

**6. Reasoning APIs.** This is where retrieval, graph traversal, and structured facts combine
into judgeable outputs: a cited, confidence-scored copilot answer; an Asset 360 view; a
compliance-gap detector; and a lessons-learned similarity search — all exposed as typed FastAPI
endpoints under one frozen contract (`MASTER_SPEC.md` §6).

**7. Frontend modules.** Seven Next.js screens each render one lens on the same underlying graph:
Dashboard, Copilot, Asset 360, Graph Explorer, Compliance Board, Lessons Learned, and Evaluation.
A single typed API client with automatic mock-data fallback means the UI never breaks even if the
backend hiccups mid-demo.

**8. Evaluation harness.** Twenty-four benchmark questions, each with expected supporting
documents and entities, are scored automatically for retrieval hit rate, citation coverage,
answer latency, and entity-linkage coverage — turning "trust us, it works" into a number a judge
can see on screen.

The throughline: every stage was built against a spec frozen *before* implementation started,
which is why the demo holds together as one coherent product instead of feeling like five
disconnected feature demos bolted together at the end.
