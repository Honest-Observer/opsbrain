# MASTER_SPEC.md — OpsBrain (Industrial Knowledge & Operations Brain)

Status: **FROZEN**. This document is the single source of truth for architecture, contracts,
and scope for the ET AI Hackathon 2026, Problem Statement 8 submission. Do not fork the
architecture described here — extend it, don't reinvent it.

## 1. Product narrative

**One line:** An Asset & Operations Brain for a plant engineer, maintenance lead, and auditor.

Industrial plants generate huge volumes of heterogeneous knowledge — SOPs, OEM manuals,
work orders, inspection reports, incident/near-miss reports, asset registries, shift handover
notes, and regulatory checklists — that lives in silos and tribal memory. OpsBrain ingests all
of it, extracts entities and relationships into a plant knowledge graph, and lets a user ask
plain-language questions and get cited, trustworthy, actionable answers. It also proactively
surfaces compliance gaps and past-incident lessons before they repeat.

## 2. User personas

- **Plant / Maintenance Engineer** — wants to know why an asset keeps failing and what to do
  before the next shutdown.
- **Maintenance Lead** — wants a prioritized view of risky assets, recurring failure patterns,
  and recommended actions across the plant.
- **Compliance / Safety Auditor** — wants to know where evidence is missing against a
  regulatory/SOP checklist and needs an exportable evidence pack.

## 3. Exact feature scope (in-scope for this prototype)

1. Universal document ingestion: PDF, TXT/MD, CSV, XLSX, JSON, and simulated scanned/image
   forms.
2. Entity extraction + relationship linking into a knowledge graph (assets, documents, people,
   failure modes, work orders, incidents, procedures, regulations).
3. Copilot Q&A with citations, confidence score, linked evidence, recommended actions.
4. Asset 360 view: maintenance history, recurring issues, likely root causes, recommended
   actions, linked documents, similar incidents, compliance issues.
5. Compliance intelligence: gap detection against a demo regulatory/SOP checklist with evidence
   coverage and severity.
6. Lessons-learned engine: similar past incident surfacing + proactive warnings.
7. Evaluation dashboard: benchmark questions, retrieval hit rate, citation coverage, latency,
   entity linkage coverage.
8. Deliverable artifacts: architecture doc, demo script, deck content, README.

## 4. Non-goals (explicitly out of scope)

- Real OCR / production-grade document AI (a deterministic heuristic simulation is enough for
  scanned forms).
- Multi-tenant auth, SSO, RBAC.
- Real regulatory database integrations — a small demo checklist is sufficient.
- Distributed infra (Kafka, microservices, Neo4j). Graph lives in Postgres/SQLite tables.
- Mobile app / native clients.
- Model fine-tuning. LLM calls (if any) are optional and must have deterministic
  rule/heuristic fallbacks so the demo never depends on an external API key being present.

## 5. Screen list (frontend)

| Screen | Must-have |
|---|---|
| Dashboard | Yes |
| Copilot | Yes |
| Asset 360 | Yes |
| Graph Explorer | Yes |
| Compliance Board | Yes |
| Lessons Learned / Prevention Feed | Yes |
| Evaluation / Benchmark page | Strong yes |

## 6. API contract list (frozen — do not rename without updating this file)

Base URL: `http://localhost:8000/api`. All responses are JSON. All list endpoints are paginated
with `limit`/`offset` optional query params (default `limit=50`, `offset=0`).

### Health
- `GET /health` → `{ "status": "ok", "version": string }`

### Ingestion
- `POST /ingestion/seed` → runs the demo seed flow (loads `data/sample_corpus` into the DB).
  Response: `{ "documents_ingested": int, "chunks_created": int, "entities_extracted": int, "relationships_created": int }`
- `GET /ingestion/status` → `{ "documents": int, "chunks": int, "entities": int, "relationships": int, "last_seeded_at": string|null }`
- `POST /ingestion/upload` (multipart file) → parses + stores a single new document.
  Response: `{ "document_id": string, "chunks_created": int }`

### Documents
- `GET /documents` → list of `{ id, title, doc_type, source_path, created_at }`
- `GET /documents/{id}` → full document with chunks

### Assets
- `GET /assets` → list of `{ id, tag, name, asset_type, criticality, open_issues, risk_score }`
- `GET /assets/{id}/three_sixty` (Asset 360) → 
  ```
  {
    "asset": { id, tag, name, asset_type, criticality, location },
    "timeline": [ { date, type, title, ref_id, summary } ],
    "recurring_issues": [ { failure_mode, count, last_seen } ],
    "similar_incidents": [ { incident_id, title, similarity, summary } ],
    "compliance_issues": [ { checklist_item, status, severity } ],
    "recommended_actions": [ { action, rationale, priority } ],
    "linked_documents": [ { id, title, doc_type } ]
  }
  ```

### Search / Reasoning
- `GET /search/semantic?q=...` → `[ { chunk_id, document_id, document_title, text, score } ]`
- `GET /graph/neighborhood?node_id=...&depth=1` → `{ nodes: [...], edges: [...] }`
- `POST /copilot/ask` body `{ "question": string }` → 
  ```
  {
    "answer": string,
    "confidence_score": float (0-1),
    "citations": [ { document_id, document_title, chunk_id, snippet } ],
    "supporting_entities": [ { id, type, label } ],
    "supporting_documents": [ { id, title } ],
    "recommended_actions": [ { action, rationale, priority } ]
  }
  ```

### Compliance
- `GET /compliance/gaps` → `[ { id, asset_tag, checklist_item, regulation_ref, status, severity, missing_evidence, corrective_action } ]`
- `GET /compliance/evidence_pack/{asset_id}` → structured export bundle (JSON manifest of
  supporting documents/entities for that asset).

### Lessons learned
- `GET /lessons?asset_id=...` → `[ { incident_id, title, summary, similarity, date, warning } ]`

### Evaluation
- `GET /eval/questions` → the benchmark set from `data/eval/questions.json`
- `POST /eval/run` → runs the benchmark and returns
  `{ "retrieval_hit_rate": float, "citation_coverage": float, "avg_latency_ms": float, "entity_linkage_coverage": float, "results": [ { question_id, passed, latency_ms } ] }`

## 7. Data model / entity schema

See `packages/shared/schema.md` (mirrored as SQLAlchemy models in
`services/api/app/models.py` and TypeScript types in `packages/shared/types.ts`). Core tables:
`assets, documents, chunks, entities, relationships, work_orders, incidents, inspections,
regulations, compliance_gaps, lessons, recommendations, benchmark_questions`.

## 8. Ingestion pipeline (contract)

1. **Load**: read raw file (PDF/TXT/MD/CSV/XLSX/JSON, or `.scan.txt` simulating an OCR'd scanned
   form).
2. **Parse**: convert to normalized `(text, metadata)`. Metadata always includes
   `doc_type, source_path, title`.
3. **Chunk**: split normalized text into ~250–400 token chunks with `chunk_index`,
   `char_start`, `char_end`.
4. **Extract entities**: regex/heuristic extraction of asset tags (`[A-Z]-?\d{2,4}` patterns
   like `P-101`, `B-12`), work order IDs (`WO-####`), incident IDs (`IR-##`), regulation refs
   (`REG-###` / `OSHA-###` style), dates, and people names from a controlled demo vocabulary.
5. **Link relationships**: create edges per the relationship contract in §9.
6. **Store**: persist documents, chunks, entities, relationships.

This must work identically whether an LLM API key is present or not — heuristic extraction is
the default and is never a "fallback to be ashamed of"; it is the primary demo-safe path.

## 9. Relationship types (graph edges)

`asset->document`, `asset->work_order`, `asset->incident`, `incident->regulation`,
`asset->procedure`, `work_order->failure_mode`, `inspection->compliance_gap`,
`incident->incident` (similarity edges for lessons-learned).

## 10. Evaluation plan

- `data/eval/questions.json`: ≥20 benchmark questions, each with `expected_document_ids`,
  `expected_entity_ids`, and `expects_citation: true`.
- `scripts/run_eval.py` (also exposed via `POST /eval/run`) computes:
  - **retrieval_hit_rate**: fraction of questions where semantic search returns ≥1 expected
    document in top-5.
  - **citation_coverage**: fraction of copilot answers that include ≥1 citation.
  - **avg_latency_ms**: mean wall-clock time of `/copilot/ask`.
  - **entity_linkage_coverage**: fraction of expected entities present in
    `supporting_entities`.

## 11. Demo flow (must work end to end)

1. `docker compose up` (or local dev scripts) → backend + frontend + db running.
2. Seed sample corpus (`POST /ingestion/seed`, one button on Dashboard or `make seed`).
3. Open Dashboard → see ingestion stats, top risky assets, recent alerts.
4. Ask Copilot: *"Why is Pump P-101 repeatedly failing?"* → cited answer + confidence +
   recommended actions.
5. Open Asset 360 for P-101 → timeline, recurring issues, similar incidents, compliance gaps.
6. Open Graph Explorer → visualize asset/doc/incident/regulation relationships.
7. Open Compliance Board → see missing evidence + severity + corrective actions.
8. Open Lessons Learned feed → proactive "resembles Incident IR-07" style warning.
9. Open Evaluation page → benchmark metrics prove it's not a fake UI.

## 12. Architecture decisions (see also DECISIONS.md)

- Monorepo: `apps/web` (Next.js+TS+Tailwind), `services/api` (FastAPI+Python),
  `packages/shared` (schema/type definitions shared conceptually across both).
- Storage: PostgreSQL + pgvector if available at runtime; automatic fallback to SQLite +
  in-process cosine-similarity vector search behind the *same* repository interface/API
  contracts, so the frontend never knows which backend is active.
- Graph lives as relational tables (`entities`, `relationships`), exposed via `/graph/*` APIs —
  no separate graph database.
- Graph UI: React Flow (lightweight, no extra backend service needed, good demo "wow" factor).
- One pluggable embedding provider wrapper (`services/api/app/embeddings.py`) — defaults to a
  deterministic local hash-based embedding so the demo never depends on network access or API
  keys; swappable for a real provider later without changing callers.
- Everything must run locally without Docker too (plain `uvicorn` + `npm run dev`), since Docker
  Desktop may not be installed on a given laptop during the hackathon.

## 13. Non-negotiable demo guardrails

- The system must never crash the UI due to missing backend data — always degrade to graceful
  empty/mock states.
- One coherent story, not three stitched demos.
