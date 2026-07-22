# ONE_PAGE_EXEC_SUMMARY.md

**OpsBrain — Industrial Knowledge & Operations Brain**
ET AI Hackathon 2026 · Problem Statement 8: AI for Industrial Knowledge Intelligence

## The problem
Industrial plants generate enormous volumes of knowledge — SOPs, manuals, work orders,
inspection reports, incident logs, handover notes, regulatory checklists — scattered across
systems and tribal memory. Recurring failures go unrecognized until they've happened three or
four times. Audits mean weeks of manual document archaeology. Retiring engineers take
undocumented judgment with them.

## The solution
OpsBrain ingests heterogeneous industrial documents, extracts entities and relationships into a
real knowledge graph, and answers plain-language questions with cited, confidence-scored,
actionable answers. It proactively surfaces compliance gaps and flags when a new incident
resembles a past one — before it repeats.

## Why it's different
- **Explainable, not a black box** — every answer traces to real source citations, with a
  "why this answer" evidence panel.
- **One graph, five capabilities** — ingestion, copilot Q&A, maintenance/RCA intelligence,
  compliance intelligence, and lessons-learned are five lenses on the same underlying graph, not
  five disconnected features.
- **Zero external dependency** — deterministic local embeddings and template-grounded answer
  synthesis mean the system runs fully offline, with no API keys and no network risk on demo day.
- **Measurably real** — an evaluation harness of 24 benchmark questions reports retrieval hit
  rate (0.875), citation coverage (1.0), entity linkage coverage (1.0), and latency (~7–12ms)
  live in the product.

## Business impact
- Faster root-cause identification → reduced maintenance downtime.
- Continuous compliance readiness → no more audit-time scrambles, one-click evidence export.
- Institutional knowledge retained in a structured, queryable graph instead of leaving with
  retiring staff.

## Scalability
Every implementation detail that matters at scale is an interface-hidden swap, not a rewrite:
SQLite → Postgres+pgvector, local embeddings → production embedding API, heuristic entity
extraction → ML-based extraction — all behind the same frozen API contracts and frontend.

## What's built (not just designed)
Full-stack working prototype: FastAPI + Python backend, Next.js + TypeScript frontend, 26-file
synthetic industrial corpus, knowledge graph, semantic search, copilot Q&A, Asset 360, Graph
Explorer, Compliance Board, Lessons Learned feed, Evaluation dashboard. Verified: 28/28 backend
tests passing, clean production frontend build, full end-to-end demo-path smoke test passing
against a live server.
