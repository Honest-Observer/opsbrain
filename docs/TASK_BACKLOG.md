# TASK_BACKLOG.md

Prioritized backlog, split by workstream. Frozen contracts are in `MASTER_SPEC.md` — implement
against them, don't renegotiate them mid-build unless truly blocked.

## backend_ingestion
- [x] Parsers: PDF, TXT/MD, CSV, XLSX, JSON, simulated scanned form (`.scan.txt`)
- [x] Normalizer → `(text, metadata)`
- [x] Chunker (~250-400 tokens, tracks char_start/char_end)
- [x] Synthetic corpus generator (26 files across all doc_types, cross-referenced IDs)
- [x] `POST /ingestion/seed`, `GET /ingestion/status`, `POST /ingestion/upload`

## backend_reasoning
- [x] Entity extractor (regex/heuristic: asset tags, WO IDs, incident IDs, regulation refs, dates, people)
- [x] Relationship/graph builder (edge types per MASTER_SPEC §9)
- [x] Local embedding provider (deterministic, pluggable) + vector store (pgvector or SQLite fallback)
- [x] `GET /search/semantic`
- [x] `GET /graph/neighborhood`
- [x] `GET /assets`, `GET /assets/{id}/three_sixty`
- [x] `POST /copilot/ask` (retrieval + citation + confidence + recommended actions)
- [x] `GET /compliance/gaps`, `GET /compliance/evidence_pack/{asset_id}`
- [x] `GET /lessons`
- [x] `data/eval/questions.json` (24 benchmark questions) + `scripts/run_eval.py` + `POST /eval/run`
- [x] Tests for ingestion + core endpoints (28 pytest tests, verified passing)

## frontend_dashboard
- [x] Landing/Dashboard: ingestion stats, alerts, top risky assets, top repeated issues, quick demo-query links
- [x] Typed API client (`apps/web/lib/api.ts`) matching MASTER_SPEC contracts exactly
- [x] Mock-safe service layer (UI loads even if backend incomplete/down)
- [x] Dark professional industrial theme, empty/loading/error states

## frontend_graph
- [x] Copilot screen (question input, suggested questions, answer card, "why this answer" drawer)
- [x] Asset 360 screen
- [x] Knowledge Graph Explorer (React Flow, click-to-inspect)
- [x] Compliance Board
- [x] Lessons Learned / Prevention Feed
- [x] Evaluation / Benchmark page

## integrations
- [x] Reconcile any contract drift between backend and frontend (fixed evidence_pack shape,
      docker-compose env var name)
- [x] End-to-end smoke test of the full demo path (`scripts/smoke_test.py`, verified passing)
- [x] Graceful degradation guardrails (missing data never crashes UI — mock-safe API client)

## demo_and_docs
- [x] docs/ARCHITECTURE.md, docs/DEMO_SCRIPT.md, docs/PITCH_STORY.md, docs/JUDGE_QA.md
- [x] docs/ARCHITECTURE_DIAGRAM.mmd, ARCHITECTURE_NARRATIVE.md, PRESENTATION_DECK_CONTENT.md,
      DEMO_VIDEO_SCRIPT.md, DEMO_SHOT_LIST.md, ONE_PAGE_EXEC_SUMMARY.md, JUDGES_HANDOUT.md
- [x] Final README run instructions (verified against a fresh venv + fresh npm install)
