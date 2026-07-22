# ARCHITECTURE.md

System design writeup for OpsBrain, as actually built and verified (not aspirational).

## 1. High-level shape

```
[Synthetic Corpus (data/sample_corpus, 26 files)]
                |
                v
        [Ingestion Pipeline]   (services/api/app/ingestion.py)
   parse PDF/TXT/MD/CSV/XLSX/JSON/.scan.txt
   -> normalize (text, metadata)
   -> chunk (~250-400 tokens, char_start/char_end tracked)
                |
     +----------+-----------+
     |                      |
     v                      v
[Chunk Store +          [Entity Extraction +
 Vector Index]           Relationship/Graph Builder]
 (SQLite/Postgres,       (regex/heuristic — asset tags, WO/IR/REG
  local hash embedding    codes, dates, people; 8 relationship types)
  + cosine similarity,
  or pgvector)
     |                      |
     +----------+-----------+
                |
                v
        [Reasoning APIs]     (services/api/app/reasoning.py)
   semantic search, graph neighborhood, asset 360, copilot Q&A
   (template-synthesized answers grounded in real retrieved
   chunks + structured DB facts — no LLM call, no API key),
   compliance gap detection, lessons-learned similarity
                |
                v
        [FastAPI HTTP layer]  (services/api/app/main.py, /api/*)
                |
                v
      [Next.js Frontend]      (apps/web)
   Dashboard, Copilot, Asset 360, Graph Explorer, Compliance
   Board, Lessons Learned, Evaluation — each backed by a typed
   API client with automatic mock-data fallback if the backend
   is unreachable (so the UI never breaks mid-demo)
                |
                v
        [Evaluation Harness]  (scripts/run_eval.py, data/eval/questions.json)
   24 grounded benchmark questions -> retrieval hit rate,
   citation coverage, latency, entity linkage coverage
```

## 2. Why this shape

- **One database, two backends behind one interface.** Postgres+pgvector is the
  "real" target; SQLite + local cosine similarity is the fallback so the demo
  never depends on Docker/Postgres being available on a given laptop
  (DECISIONS.md ADR-004). The frontend and every API contract are identical
  either way.
- **Graph as relational tables, not a graph database.** `entities` +
  `relationships` tables give a genuine, queryable, visualizable knowledge
  graph without operating a separate graph engine (ADR-005).
- **Heuristic entity extraction is the primary path, not a fallback bolted on
  after an LLM call fails.** It is deterministic and fully reproducible, which
  matters more for a judged demo than marginal extraction recall (ADR-007).
- **No external API keys anywhere.** Embeddings are a local deterministic
  hash-based scheme; copilot answers are template-synthesized from real
  retrieved evidence. This means the demo works completely offline, on any
  machine, with zero setup risk on demo day.
- **Mock-safe frontend.** Every API client function catches failures and
  falls back to realistic seeded mock data, so a backend hiccup during a live
  demo degrades to a "Demo Mode" banner instead of a broken screen.

## 3. Data flow for the signature demo question

"Why is Pump P-101 repeatedly failing?" →
1. Frontend Copilot screen calls `POST /api/copilot/ask`.
2. Backend runs semantic search over chunk embeddings, pulls structured facts
   from `work_orders`/`incidents` for asset P-101 (WO-1041 → WO-1052 →
   WO-1067, near-miss IR-03, incident IR-07, fix WO-1089).
3. Answer is synthesized from that evidence with citations, a confidence
   score, supporting entities, and recommended actions.
4. Clicking through to Asset 360 re-uses the same underlying data via
   `/assets/{id}/three_sixty` — timeline, recurring issues, similar
   incidents, compliance issues, and recommended actions all trace back to
   the same seeded corpus, so the story is consistent across every screen.

## 4. Tech stack (as built)

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + React Flow |
| Backend | FastAPI + Pydantic + SQLAlchemy (Python 3.12) |
| Database | SQLite (default/tested) with automatic Postgres+pgvector path if `DATABASE_URL` is set and reachable |
| Embeddings | Deterministic local signed feature-hashing (256-dim), no network dependency |
| Graph | Relational `entities`/`relationships` tables, exposed via `/graph/neighborhood` (BFS) |
| Graph UI | React Flow |
| Evaluation | Custom harness (`scripts/run_eval.py`, `data/eval/questions.json`) |
| Deployment | Docker Compose (Postgres+pgvector, API, web) or fully local (`uvicorn` + `npm run dev`), no Docker required |

## 5. Verified quality signals

- 28/28 backend pytest tests passing.
- Full demo-path smoke test (`scripts/smoke_test.py`) passing end-to-end
  against a live server.
- Evaluation harness on the seeded corpus: retrieval hit rate 0.875, citation
  coverage 1.0, entity linkage coverage 1.0, average copilot latency ~7–12ms
  server-side.
- Frontend production build (`npm run build`) compiles cleanly; all 7 routes
  verified returning HTTP 200.
