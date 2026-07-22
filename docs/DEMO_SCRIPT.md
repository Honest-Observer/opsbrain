# DEMO_SCRIPT.md

Live 5-minute demo sequence. Rehearse this exact path — it's the one MASTER_SPEC.md §11 was
designed around and the one the smoke test (`scripts/smoke_test.py`) verifies end to end.

## Before you start

```bash
# Terminal 1 — backend
cd services/api
.venv/Scripts/activate      # or: source .venv/Scripts/activate on Git Bash
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd apps/web
npm run dev
```

Open http://localhost:3000/dashboard. If the corpus isn't seeded yet, the Dashboard's "Seed
Demo Corpus" action calls `POST /api/ingestion/seed` — click it once before you go live, or run
`curl -X POST http://localhost:8000/api/ingestion/seed`.

## The 5-minute sequence

**0:00 – Dashboard (30s)**
"This is OpsBrain — an Asset & Operations Brain for a plant engineer, maintenance lead, and
auditor. It's already ingested 26 real-shaped industrial documents: SOPs, OEM manuals, work
orders, inspection reports, incident logs, an asset registry, shift handover notes, and a
regulatory checklist." Point at the ingestion stats, top risky assets (P-101 and B-12 at the
top), and recent alerts.

**0:30 – Copilot (90s)**
Click the seeded quick prompt: *"Why is Pump P-101 repeatedly failing?"*
"Notice this isn't a generic chatbot answer — it's grounded in citations from actual incident
reports and work orders." Point out:
- The confidence meter (0.87).
- Citations linking to IR-07, WO-1042, the pump SOP, and IR-11.
- Recommended actions (cartridge seal upgrade, minimum-flow interlock).
- Expand "Why this answer" to show the retrieved evidence and reasoning trace in plain English.

**2:00 – Asset 360 (60s)**
Click through to the P-101 Asset 360 page.
"Here's the full picture for this asset: the maintenance timeline shows the exact failure
pattern — WO-1041, WO-1052, WO-1067, near-miss IR-03, incident IR-07, then the preventive fix
WO-1089. Recurring issues, similar past incidents, and recommended actions are all one click
away."

**3:00 – Graph Explorer (45s)**
Open the Graph Explorer, centered on P-101.
"This is the actual knowledge graph, not a mockup — assets, documents, work orders, incidents,
and regulations are real linked nodes. Click a node to see what connects to what." Click the
IR-07 incident node to show its linked SOP and regulation.

**3:45 – Compliance Board (45s)**
Open the Compliance Board.
"Boiler B-12 has a real compliance gap: the annual relief-valve bench-test certificate is
missing for 2025. Severity is flagged high, and here's the exact corrective action and the
evidence pack you'd hand an auditor." Click "Export Evidence Pack" if wired.

**4:30 – Lessons Learned + Evaluation (30s)**
Open Lessons Learned: "This is the proactive layer — the system surfaces that IR-07 resembles
the earlier near-miss IR-03, before it becomes a bigger problem." Then flash the Evaluation
page: "And this isn't a fake UI — retrieval hit rate 0.875, citation coverage 1.0, entity
linkage coverage 1.0, sub-15ms average response time, all measured against 24 benchmark
questions."

**Close (15s)**
"One system, one flow, one story: upload plant knowledge, build the graph, answer clearly,
recommend action, and prove compliance and lessons learned — end to end."

## Things to avoid clicking live

- Don't demo `/documents/{id}` raw JSON in a browser tab — it's functional but not
  presentation-polished.
- Don't re-run `/ingestion/seed` mid-demo unless you mean to reset IDs are deterministic, so
  re-seeding is safe, but it does take a couple of seconds and briefly shows an empty state.
- If backend is down for any reason, every screen still renders via mock-data fallback — the
  "Demo Mode" banner will show, keep talking, it will not crash.
