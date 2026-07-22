# OpsBrain — Industrial Knowledge & Operations Brain

ET AI Hackathon 2026 — Problem Statement 8: *AI for Industrial Knowledge Intelligence:
Unified Asset & Operations Brain.*

OpsBrain ingests heterogeneous industrial documents (SOPs, work orders, inspection reports,
incident logs, asset registries, handover notes, regulatory checklists), builds a plant
knowledge graph, and answers plain-language questions with cited, trustworthy, actionable
answers — plus proactive compliance-gap and lessons-learned surfacing.

See `MASTER_SPEC.md` for the full architecture and API contracts, `docs/DEMO_SCRIPT.md` for the
live demo walkthrough, `docs/ARCHITECTURE.md` for the system design writeup, `docs/PITCH_STORY.md`
for the pitch narrative, and `docs/JUDGE_QA.md` for anticipated judge questions.

## Quick start (no Docker required)

### 1. Backend

```bash
cd services/api
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

#### (Recommended) Enable the Gemini-powered RAG

OpsBrain runs fully offline out of the box (deterministic local embeddings + template answers).
To unlock the real RAG — Gemini embeddings, free-form cited answers to *any* question, and
LLM knowledge-graph extraction over arbitrary uploaded documents — add a
[Google AI Studio](https://aistudio.google.com/apikey) key:

```bash
cd services/api
cp .env.example .env
# edit .env and set GEMINI_API_KEY=<your key>   (classic AIza... or newer AQ.* both work)
```

Restart the backend and re-seed (`curl -X POST http://localhost:8000/api/ingestion/seed`) so the
corpus is embedded with Gemini. `GET /api/health` will report `"ai_mode": "gemini"`, and the app
header shows a green **Gemini AI: Live** badge. Defaults: `gemini-3.5-flash` for answers,
`gemini-embedding-001` for embeddings (override via `GEMINI_CHAT_MODEL` / `GEMINI_EMBED_MODEL`
in `.env`). Without a key everything still works — just in offline heuristic mode.

> Security: `.env` is git-ignored — never commit your key. Treat any key you've shared as
> compromised and rotate it.

Backend health check: http://localhost:8000/api/health. Seed the demo corpus with
`curl -X POST http://localhost:8000/api/ingestion/seed` (or click "Seed Demo Corpus" on the
Dashboard once the frontend is running).

Run the backend test suite: `.venv/Scripts/python -m pytest tests/ -v` (28 tests).

Run the evaluation harness: `.venv/Scripts/python ../../scripts/run_eval.py`.

Run the full end-to-end demo-path smoke test (backend must be running):
`python scripts/smoke_test.py` from the repo root.

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 (redirects to `/dashboard`).

### 3. (Optional) Docker Compose — Postgres + pgvector instead of SQLite

```bash
docker compose up --build
```

## Demo path

1. Open the Dashboard — corpus is pre-seeded.
2. Ask the Copilot: *"Why is Pump P-101 repeatedly failing?"* (with Gemini enabled, also try a
   totally free-form question like *"Compare the maintenance risk of the pumps versus the boiler
   and tell me what to prioritize before the next shutdown."*)
3. Open Asset 360 for P-101.
4. Open the Graph Explorer.
5. Open the Compliance Board.
6. Open the Lessons Learned feed.
7. Open the Evaluation page.
8. (Gemini) Open **Ingest**, drag in any raw document, then ask the Copilot about it — the
   system parses, embeds, and graph-extracts it live, then answers questions grounded in it.

## Repo layout

```
apps/web           Next.js + TypeScript + Tailwind frontend
services/api       FastAPI + Python backend
packages/shared     Shared schema/type definitions
data/sample_corpus  Synthetic demo industrial documents
data/eval           Benchmark questions for the evaluation harness
docs                Architecture, demo script, pitch, deliverables
scripts             Dev/ops scripts (seeding, evaluation)
```

## Status

See `STATUS.md` for the running build log and `DECISIONS.md` for architecture decision
records.
