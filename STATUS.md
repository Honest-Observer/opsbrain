# STATUS.md

Live status log. Append new entries at the top. Do not delete history.

---

## 2026-07-22 — Gemini-powered RAG upgrade (real embeddings + generation + LLM graph extraction)

Turned the offline-heuristic prototype into a true, fully-functional RAG system while keeping
the offline path as a guaranteed fallback. Gated entirely on a `GEMINI_API_KEY` in a git-ignored
`services/api/.env` (see `.env.example`).

- **New `app/config.py`**: loads `.env` (python-dotenv), exposes `gemini_enabled()`, model names,
  and `ai_mode()`. Honors `OPSBRAIN_DISABLE_GEMINI` (used by conftest to keep tests offline).
- **New `app/gemini_client.py`**: REST wrapper (`x-goog-api-key` auth — works for classic
  `AIza...` and newer `AQ.*` keys). `embed()` (L2-normalized), `generate_json()` (structured
  output with `responseSchema`, `thinkingLevel: low`, 8192-token budget, lenient JSON salvage),
  `generate_text()`.
- **`app/embeddings.py`**: added `GeminiEmbeddingProvider` (`gemini-embedding-001`, 768-dim).
  `get_embedding_provider()` returns it when a key is present, else the local hash provider —
  no other code changes since it's behind the existing interface.
- **`app/reasoning.py`**: `copilot_ask` now dispatches to `_copilot_ask_gemini` (real RAG:
  retrieve top-8 chunks → grounded `gemini-3.5-flash` generation → cite by source) with the
  original deterministic `_copilot_ask_local` as fallback. Answers arbitrary NL queries.
- **New `app/extraction_llm.py`** + upload endpoint: uploaded raw documents get LLM
  entity+relationship extraction into the knowledge graph, so brand-new data is immediately
  queryable and graphed.
- **`app/main.py`**: `/api/health` now reports `ai_mode`/`ai_model`/`gemini_enabled`; upload
  returns entities/relationships created + ai_mode.
- **`app/eval_engine.py`**: scores on the fast local composer over the real Gemini embeddings, so
  a full 24-question benchmark run stays fast/free/reproducible instead of firing 24 LLM calls.
- **Frontend**: new `/ingest` page (drag-drop raw-data upload showing chunks/entities/relationships
  extracted); `DemoModeBanner` now shows a live "Gemini AI: Live (model)" vs "Offline heuristic"
  badge from `/api/health`.

Verified live (real Gemini key):
- `/api/health` → `ai_mode: gemini`, model `gemini-3.5-flash`.
- Seeded 26 docs with real Gemini embeddings.
- Arbitrary analytical queries (e.g. "compare pump vs boiler risk and tell me what to prioritize")
  return correct, multi-document, cited answers — not templated.
- Uploaded a brand-new handover note the system had never seen → 6 entities + 12 relationships
  extracted → copilot correctly answered a question about it, citing the uploaded doc.
- Benchmark: retrieval_hit_rate improved 0.875 → **1.0** with Gemini embeddings; citation &
  entity-linkage coverage 1.0.
- Full demo-path smoke test passes end-to-end against the live Gemini backend (12/12).
- Offline path still green: 28/28 pytest with Gemini force-disabled; frontend `npm run build`
  clean with the new `/ingest` route.

---

## 2026-07-22 — Final hackathon submission deliverables produced

Executed the plan's final "deliverables prompt": generated all 7 required submission artifacts
under `docs/`:
- `ARCHITECTURE_DIAGRAM.mmd` (Mermaid flowchart: ingestion → chunking → entity extraction →
  graph storage → vector/search → reasoning APIs → frontend modules → evaluation harness)
- `ARCHITECTURE_NARRATIVE.md`
- `PRESENTATION_DECK_CONTENT.md` (11 slides)
- `DEMO_VIDEO_SCRIPT.md` (~3:30–4:00 runtime)
- `DEMO_SHOT_LIST.md`
- `ONE_PAGE_EXEC_SUMMARY.md`
- `JUDGES_HANDOUT.md` (includes judging-criteria alignment table, status-quo comparison, Q&A
  highlights, and the final submission checklist)

Marked every item in `docs/TASK_BACKLOG.md` complete. All 6 workstreams
(backend_ingestion, backend_reasoning, frontend_dashboard, frontend_graph, integrations,
demo_and_docs) are done. Repo is demo-ready: two things remain and are intentionally left as
manual human tasks (not something to fake) — recording the actual demo video and capturing the
actual screenshots for the deck, both scripted in detail above.

---

## 2026-07-22 — Integration, hardening, and doc pass complete

- Independently re-verified the backend build from a fresh venv (not just trusting the build
  report): 28/28 pytest tests pass, `/api/health`, `/api/ingestion/seed`, `/api/copilot/ask`,
  `/api/assets/{id}/three_sixty`, `/api/graph/neighborhood`, `/api/compliance/gaps`,
  `/api/compliance/evidence_pack/{id}`, `/api/lessons`, and `/api/eval/run` all verified live
  over real HTTP.
- Independently re-verified the frontend build: found and fixed a real TypeScript build error in
  `lib/mockData.ts` (three `DocumentRef` mocks were missing the required `doc_type` field) that
  the frontend build agent's self-report had missed. `npm run build` now compiles clean; all 7
  routes (`/dashboard`, `/copilot`, `/assets/[id]`, `/graph`, `/compliance`, `/lessons`,
  `/evaluation`) verified returning HTTP 200 against a production build.
- Found and fixed a real contract mismatch: `apps/web/lib/api.ts`'s `EvidencePack` type and mock
  fallback didn't match the backend's actual `/compliance/evidence_pack/{id}` response shape
  (backend returns `asset_tag`, `asset_name`, `compliance_gaps`, `linked_documents`,
  `supporting_entities`; frontend type expected `documents`/`entities`). Fixed the frontend type
  and mock fallback to match the real backend shape.
- Found and fixed an env var name mismatch: `docker-compose.yml` set
  `NEXT_PUBLIC_API_BASE_URL` but `apps/web/lib/api.ts` reads `NEXT_PUBLIC_API_BASE`. Fixed
  docker-compose.yml.
- Added `scripts/smoke_test.py`: a dependency-free end-to-end smoke test that walks the exact
  demo path from MASTER_SPEC.md §11 (seed -> assets -> copilot ask on P-101 -> asset 360 ->
  graph neighborhood -> compliance gaps -> evidence pack -> lessons learned -> eval run) against
  a live server. Verified passing.
- Verified CORS preflight works correctly for cross-origin frontend->backend calls
  (`access-control-allow-origin: *`).
- Wrote `docs/ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md`, `docs/PITCH_STORY.md`, `docs/JUDGE_QA.md`.
- Updated `README.md` with exact verified run commands (venv activation, test/eval/smoke-test
  commands) so a non-expert judge or mentor can run the project.
- Next: final hackathon submission deliverables (architecture diagram, deck content, demo video
  script, exec summary, judges handout, submission checklist).

---

## 2026-07-22 — Backend fully implemented (services/api, data/, scripts/)

Built the entire OpsBrain backend end to end, against the frozen MASTER_SPEC.md /
DECISIONS.md / schema.md contracts. Scope touched: `services/api/**`, `data/**`,
`scripts/**` only (did not touch `apps/web/**`).

- **Models** (`services/api/app/models.py`): all 13 tables from `schema.md` as
  SQLAlchemy models (assets, documents, chunks, entities, relationships,
  work_orders, incidents, inspections, regulations, compliance_gaps, lessons,
  recommendations, benchmark_questions), plus an `ingestion_runs` bookkeeping
  table for `last_seeded_at`.
- **DB layer** (`app/db.py`, ADR-004): tries `DATABASE_URL` (Postgres) first,
  auto-falls back to `services/api/opsbrain.db` (SQLite) if unset/unreachable.
  Vector search wrapped behind a `VectorBackend` interface — `PgVectorBackend`
  (pgvector `<=>`, only used if the extension is actually creatable) vs.
  `NumpyCosineBackend` (JSON-encoded float list + numpy cosine, default/tested
  path since this box has no Postgres/Docker).
- **Embeddings** (`app/embeddings.py`, ADR-008): deterministic local hash
  embedding (256-dim signed feature hashing over stopword-filtered tokens,
  with a weight boost for domain codes like `p-101`/`wo-1041`). No network,
  no API key, fully reproducible.
- **Synthetic corpus** (`app/corpus_generator.py` → `data/sample_corpus/`):
  26 internally-consistent files across sop/manual/work_order/inspection/
  incident/asset_registry/handover_note/regulation, covering PDF, MD, JSON,
  CSV, XLSX, TXT, and `.scan.txt`. Central story: Pump P-101 has 3 recurring
  mechanical-seal-failure work orders (WO-1041/1052/1067) + near-miss IR-03 +
  incident IR-07 + preventive fix WO-1089; Boiler B-12 has a real compliance
  gap (missing 2025 relief-valve V-045 bench-test certificate vs. REG-052/
  REG-014), surfaced via the Q4 inspection report.
- **Ingestion** (`app/ingestion.py`): parsers for all required formats,
  ~300-word chunker tracking exact char_start/char_end, and regex/heuristic
  entity extraction (ADR-007 — primary path, not a fallback) for asset tags,
  WO/IR/REG codes, dates, and a controlled people vocabulary.
- **Seeding + graph** (`app/seed.py`): seeds structured operational tables
  directly from the corpus generator's canonical data, then actually runs
  the ingestion pipeline over every generated file to build
  documents/chunks/entities/relationships (all 8 relationship types from
  §9, including embedding-similarity-driven `incident->incident` lessons
  edges). All document/entity IDs are deterministic (uuid5 of a natural
  key) so `data/eval/questions.json` can hardcode expected IDs that survive
  reseeding.
- **Reasoning** (`app/reasoning.py`): semantic search, graph neighborhood
  (BFS over relationships), copilot Q&A (template-synthesized answer,
  grounded in real retrieved chunks + structured asset/WO/incident data —
  no LLM call, per the non-goals section), asset 360, compliance gaps +
  evidence pack, lessons-learned.
- **API** (`app/main.py`): every endpoint in MASTER_SPEC §6 implemented
  under `/api`, exact response shapes.
- **Eval** (`data/eval/questions.json` — 24 questions; `app/eval_engine.py`;
  `scripts/run_eval.py` CLI wrapper; wired into `POST /api/eval/run`).
  Current numbers against the seeded corpus: retrieval_hit_rate 0.875,
  citation_coverage 1.0, entity_linkage_coverage 1.0, avg_latency_ms ~7-12ms.
- **Tests** (`services/api/tests/`): 28 pytest tests (ingestion unit tests +
  full API integration tests against a seeded isolated SQLite DB), all
  passing on a freshly-created venv (`services/api/.venv`) built from
  `services/api/requirements.txt`.
- Manually booted `uvicorn app.main:app` and confirmed `/api/health`,
  `POST /api/ingestion/seed`, `GET /api/ingestion/status`,
  `POST /api/copilot/ask`, `GET /api/compliance/gaps`, and
  `POST /api/eval/run` all work over real HTTP, then stopped the server.
- Fixed one real bug found during manual verification: `run_seed`'s
  returned `relationships_created` count undercounted (session autoflush
  was off, so `db.query(Relationship).count()` didn't see just-added rows)
  — added an explicit `db.flush()` before the count queries.
- Next: frontend (`apps/web`) integration against these exact contracts;
  see the handoff report for full endpoint list, deviations, and
  assumptions.

## 2026-07-22 — Repo constitution frozen

- Created monorepo skeleton: `apps/web`, `services/api`, `packages/shared`, `data/sample_corpus`,
  `data/eval`, `docs`, `scripts`.
- Wrote `MASTER_SPEC.md` (frozen architecture, API contracts, data model, demo flow).
- Wrote `DECISIONS.md`.
- Next: scaffold placeholder apps + shared schema + task backlog, then build backend and
  frontend in parallel.

