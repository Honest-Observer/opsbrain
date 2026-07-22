# PRESENTATION_DECK_CONTENT.md

11 slides. Content only — build the visual deck from this in whatever tool you prefer (see
`DEMO_SHOT_LIST.md` for the screenshots to drop in).

---

### Slide 1 — Title
**OpsBrain — Industrial Knowledge & Operations Brain**
ET AI Hackathon 2026 · Problem Statement 8: AI for Industrial Knowledge Intelligence
*Subtitle:* An Asset & Operations Brain for a plant engineer, maintenance lead, and auditor.

### Slide 2 — The problem
- Industrial knowledge is fragmented across SOPs, manuals, work orders, incident logs, and
  tribal memory.
- Retiring engineers take undocumented judgment with them.
- Recurring failures go unrecognized until the third or fourth occurrence.
- Audits mean weeks of manual document archaeology.

### Slide 3 — The insight
Five "required capabilities" in the brief aren't five features — they're five views into one
graph of the same operational reality. Build the graph once; every capability is a lens on it.

### Slide 4 — What we built
One system, one flow, one story: **upload plant knowledge → build the graph → answer clearly →
recommend action → prove compliance and lessons learned.**
Screens: Dashboard, Copilot, Asset 360, Graph Explorer, Compliance Board, Lessons Learned,
Evaluation.

### Slide 5 — Architecture (drop in `ARCHITECTURE_DIAGRAM.mmd` render)
Ingestion → parsing/chunking → entity extraction → knowledge graph → vector/search layer →
reasoning APIs → frontend → evaluation harness. No external API keys anywhere — fully
deterministic and offline-safe.

### Slide 6 — Live capability: the Copilot
*(screenshot: Copilot answer card for "Why is Pump P-101 repeatedly failing?")*
Cited answer, confidence score (0.87), linked entities, recommended actions — not a black box.

### Slide 7 — Live capability: Asset 360 + Graph Explorer
*(screenshots: Asset 360 for P-101, Graph Explorer centered on P-101)*
Full maintenance timeline, recurring failure pattern, and the actual knowledge graph — clickable,
not a static diagram.

### Slide 8 — Live capability: Compliance + Lessons Learned
*(screenshots: Compliance Board showing the B-12 relief-valve gap, Lessons Learned feed)*
Real compliance gap detection with evidence-pack export; proactive "this resembles a past
incident" warnings.

### Slide 9 — Proof it's not a fake UI
*(screenshot: Evaluation page)*
24 benchmark questions · retrieval hit rate 0.875 · citation coverage 1.0 · entity linkage
coverage 1.0 · ~7–12ms average answer latency.

### Slide 10 — Business impact & scalability
- Faster root-cause identification on recurring failures → maintenance downtime reduction.
- Continuous compliance readiness instead of audit-time scrambles.
- Institutional knowledge retained in a structured, queryable graph, not tribal memory.
- Scales by swapping interchangeable parts (SQLite→Postgres+pgvector, local embeddings→
  production embedding API, heuristic extraction→ML extraction) with zero API/contract changes.

### Slide 11 — Status quo vs. OpsBrain
| Status quo | OpsBrain |
|---|---|
| Scattered files, manual search | Unified knowledge graph |
| Tribal knowledge, lost at retirement | Persistent, queryable memory |
| Weeks of manual audit evidence-gathering | One-click evidence pack |
| Repeated incidents | Proactive lessons-learned warnings |
| "Trust me" AI | Every answer cited to real source evidence |
