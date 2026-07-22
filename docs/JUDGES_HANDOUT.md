# JUDGES_HANDOUT.md

*Printable one-pager for judges/mentors — pairs with `ONE_PAGE_EXEC_SUMMARY.md`.*

## OpsBrain — Industrial Knowledge & Operations Brain
Problem Statement 8: AI for Industrial Knowledge Intelligence — Unified Asset & Operations Brain

**One line:** An Asset & Operations Brain for a plant engineer, maintenance lead, and auditor —
one graph, five judged capabilities, zero external API dependency.

## Try it yourself
```
cd services/api && .venv/Scripts/python -m uvicorn app.main:app --port 8000   # backend
cd apps/web && npm run dev                                                     # frontend
```
Open http://localhost:3000, click "Seed Demo Corpus," then ask the Copilot: *"Why is Pump P-101
repeatedly failing?"* Full instructions: `README.md`.

## Judging-criteria alignment

| Criterion | Where it shows up |
|---|---|
| Innovation (25%) | One knowledge graph powering five capabilities, not five bolted-on demos; proactive lessons-learned warnings; fully offline/deterministic architecture |
| Business Impact (25%) | Recurring-failure root cause surfaced (P-101), real compliance gap caught (B-12), one-click evidence export |
| Technical Excellence (20%) | Real ingestion across 7+ formats, real entity/relationship extraction, real semantic search, 28/28 backend tests, evaluation harness with measured metrics |
| Scalability (15%) | Every implementation detail (DB, embeddings, extraction) is an interface-hidden swap behind frozen API contracts |
| User Experience (15%) | Dark, enterprise-grade UI; citations/confidence on every answer; graceful degradation if backend is unavailable |

## Comparison against the status quo

| Status quo | OpsBrain |
|---|---|
| Scattered files, manual search | Unified knowledge graph across all document types |
| Tribal knowledge, lost at retirement | Persistent, queryable institutional memory |
| Weeks of manual audit evidence-gathering | One-click evidence pack export |
| Repeated incidents | Proactive lessons-learned warnings |
| "Trust me" AI answers | Every answer cited to real source evidence |

## Likely questions and crisp answers

See `docs/JUDGE_QA.md` for the full set. Highlights:

- **"Is this a real LLM?"** — Retrieval, extraction, and graph construction are all real and
  deterministic; answer synthesis is template-grounded in real retrieved evidence rather than an
  external LLM call, by design, for offline reproducibility. The architecture supports swapping
  in a real LLM/embedding API behind the same interface with zero contract changes.
- **"How do you know the citations are real?"** — The evaluation harness measures citation
  coverage directly: 1.0 across 24 benchmark questions, enforced by `POST /api/eval/run`, not
  self-asserted.
- **"What if the backend fails during the demo?"** — Every screen has a mock-data fallback; the
  UI shows a "Demo Mode" banner instead of breaking.

## Final submission checklist

- [x] Working prototype (backend + frontend), runnable locally without Docker
- [x] Architecture diagram (`docs/ARCHITECTURE_DIAGRAM.mmd`) + narrative (`docs/ARCHITECTURE_NARRATIVE.md`)
- [x] Presentation deck content (`docs/PRESENTATION_DECK_CONTENT.md`, 11 slides)
- [x] Demo video script (`docs/DEMO_VIDEO_SCRIPT.md`, ~3:30–4:00) + shot list (`docs/DEMO_SHOT_LIST.md`)
- [x] One-page executive summary (`docs/ONE_PAGE_EXEC_SUMMARY.md`)
- [x] Judges handout (this file) + full Q&A prep (`docs/JUDGE_QA.md`)
- [x] README with exact run commands verified by independent testing
- [x] MASTER_SPEC.md / DECISIONS.md / STATUS.md kept current throughout the build
- [x] Backend test suite passing (28/28) — verified independently, not just self-reported
- [x] Frontend production build clean — verified independently, one real type error found and fixed
- [x] End-to-end demo-path smoke test passing against a live server (`scripts/smoke_test.py`)
- [x] Evaluation harness producing real, non-trivial metrics (`data/eval/questions.json`, `scripts/run_eval.py`)
- [ ] Record the actual demo video following `docs/DEMO_VIDEO_SCRIPT.md`
- [ ] Capture the actual screenshots listed in `docs/DEMO_SHOT_LIST.md` and drop into the deck
- [ ] Do one full dry-run of the live 5-minute demo (`docs/DEMO_SCRIPT.md`) before presenting
