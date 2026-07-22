# DECISIONS.md

Architecture decision records (ADR-lite). One entry per decision. Append-only.

---

### ADR-001: Monorepo over polyrepo
**Decision:** Single repo with `apps/web`, `services/api`, `packages/shared`.
**Why:** 30-hour sprint; polyrepo coordination overhead is pure waste for a 1-person build.

### ADR-002: FastAPI + Python backend
**Decision:** FastAPI + Pydantic + SQLAlchemy.
**Why:** Best ecosystem fit for document parsing, retrieval, and reasoning code; fast to
scaffold; typed request/response models map cleanly to the frozen API contract.

### ADR-003: Next.js + TypeScript + Tailwind frontend
**Decision:** Next.js App Router + TS + Tailwind.
**Why:** Fastest path to a polished, demo-grade UI with good defaults for loading/empty states.

### ADR-004: Postgres+pgvector with automatic SQLite fallback
**Decision:** Try Postgres+pgvector first; if unreachable at startup, fall back to SQLite with
an in-process cosine similarity vector search, behind the same repository interface.
**Why:** Docker/Postgres may not be available on every dev machine; the demo must never be
blocked by infra. API contracts stay identical either way.

### ADR-005: Knowledge graph as relational tables, not a graph DB
**Decision:** `entities` + `relationships` tables, exposed via `/graph/*` endpoints.
**Why:** Avoids Neo4j operational overhead; still gives a real, queryable, visualizable graph
for the demo.

### ADR-006: React Flow for graph visualization
**Decision:** React Flow over Cytoscape.
**Why:** Simpler React-native integration, sufficient performance for demo-sized graphs
(hundreds of nodes), less time to a good-looking result.

### ADR-007: Heuristic/regex entity extraction as the primary path, not a "fallback"
**Decision:** Deterministic rule/regex extraction is the default extraction mechanism, not a
degraded fallback behind an LLM call.
**Why:** Demo must be 100% reproducible offline with no API key dependency. An optional LLM
extraction path can be layered in later behind the same interface without changing contracts.

### ADR-008: Pluggable local embedding provider
**Decision:** Deterministic hash-based local embedding function used by default; wrapped behind
a single provider interface so a real embedding API can be swapped in later.
**Why:** No external dependency required for the demo to run; avoids lock-in.

### ADR-009: Docker Compose optional, not required
**Decision:** Provide `docker-compose.yml`, but every service must also run via plain
`uvicorn`/`npm run dev` without Docker.
**Why:** Docker Desktop may not be installed; local dev path must never be blocked.

### ADR-011: Gemini-powered RAG as an opt-in upgrade over the offline core
**Decision:** Integrate the Google Gemini API (Google AI Studio) behind the *same* pluggable
interfaces ADR-007/008 already defined, gated on a `GEMINI_API_KEY`:
- **Embeddings**: `gemini-embedding-001` (768-dim) replaces the local hash embedding when a key
  is present (`GeminiEmbeddingProvider` in `embeddings.py`). Measurably better retrieval
  (benchmark retrieval_hit_rate rose from 0.875 → 1.0).
- **Copilot answers**: real RAG — retrieve top-k chunks over the (Gemini) embeddings, ground a
  `gemini-3.5-flash` generation on them with structured JSON output, cite by source. Answers ANY
  free-form NL query, not just pre-baked ones (`_copilot_ask_gemini` in `reasoning.py`).
- **Arbitrary-document graph extraction**: uploaded raw files get LLM entity+relationship
  extraction (`extraction_llm.py`) so brand-new data becomes queryable and graphed.
**Why:** The offline heuristic core is great for a guaranteed-reproducible demo, but the brief
asks for a system that ingests arbitrary heterogeneous data and answers arbitrary queries — that
needs real embeddings + real generation. Auth is `x-goog-api-key` (works for classic `AIza...`
and newer `AQ.*` keys). The key lives only in a git-ignored `services/api/.env`.
**Fallback is non-negotiable:** with no key (or on any Gemini/network failure) every path
degrades to the deterministic offline implementation, so the demo never hard-fails. The eval
harness deliberately scores on the fast local composer (over real Gemini embeddings) so a full
benchmark run stays fast, free, and reproducible. The test suite forces Gemini off
(`OPSBRAIN_DISABLE_GEMINI=1` in conftest) to stay hermetic.

### ADR-010: One person doing all roles (no Antigravity teammates)
**Decision:** All build phases (architecture, backend, frontend, integration, deliverables) are
executed sequentially/in parallel by the same agent (Claude Code) rather than split across
separate tools/teammates.
**Why:** Per user instruction — no multi-tool team split; the plan's *structure* (frozen spec →
parallel backend/frontend build → integration → deliverables) is preserved even though the
tooling isn't split across people.
