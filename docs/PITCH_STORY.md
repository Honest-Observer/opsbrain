# PITCH_STORY.md

## The problem

Industrial plants generate enormous volumes of knowledge — SOPs, OEM manuals, work orders,
inspection reports, incident logs, shift handover notes, regulatory checklists — and almost
none of it talks to the rest. A pump has failed four times over fourteen months, and the
evidence trail exists, but it's scattered across four different systems and two retired
engineers' memories. When someone finally connects the dots, it's usually after an outage, not
before one. Audits become weeks of manual document archaeology. Institutional knowledge leaves
with retirements.

## The insight

The judging brief calls for five things — universal ingestion, a knowledge graph, an expert
copilot, maintenance/RCA intelligence, and compliance intelligence — and the naive read is "five
features, five demos." The real insight is that these aren't five features. They're five views
into **one graph of the same underlying operational reality**. A pump's seal failure, the work
order that fixed it, the SOP that was violated, the regulation that governs it, and the near-miss
that warned about it beforehand are all the same event seen from different angles. Build the
graph once, and every "capability" is just a different lens on it.

## What we built

**OpsBrain** — an Asset & Operations Brain for a plant engineer, maintenance lead, and auditor.
Upload heterogeneous industrial documents, and OpsBrain extracts entities and relationships into
a real knowledge graph, then lets you ask plain-language questions and get answers with
citations, a confidence score, and recommended actions — not a black box. It proactively
surfaces compliance gaps against a regulatory checklist and flags when a new incident resembles
one from the past, before it repeats.

Everything runs with zero external API keys and zero network dependency — deterministic
retrieval and template-grounded answer synthesis mean the demo is 100% reproducible, which
matters as much as raw capability when you're being judged live.

## Comparison against the status quo

| Status quo | OpsBrain |
|---|---|
| Scattered files across shared drives, email, and paper | Unified knowledge graph across all document types |
| Manual keyword search, if any search at all | Cited, confidence-scored semantic answers |
| Tribal knowledge that leaves with retirements | Persistent, queryable institutional memory |
| Weeks of manual evidence-gathering for audits | One-click evidence pack export |
| Repeated incidents because no one remembers the last one | Proactive lessons-learned warnings |
| "Trust me" AI answers | Every answer traces back to real source documents |

## Business impact

- **Downtime reduction**: faster root-cause identification on recurring failures (P-101's
  four-failure pattern would have been visible after the second occurrence, not the fourth).
- **Audit readiness**: compliance gaps surfaced continuously instead of discovered at audit
  time, with an exportable evidence pack.
- **Knowledge retention**: institutional knowledge captured in a structured graph instead of
  living only in retiring engineers' heads.
- **Explainability as a feature, not a compliance checkbox**: every recommendation is traceable
  to source evidence, which is what makes an AI system usable in a regulated industrial
  environment.

## Scalability

The architecture is deliberately boring where it counts: one relational database holds
documents, chunks, entities, and relationships behind a single API layer. Swapping the local
embedding provider for a production embedding API, or SQLite for Postgres+pgvector, or the
heuristic extractor for an LLM-based one, requires no changes to the API contracts or the
frontend — every one of those is an interface-hidden implementation detail (see
DECISIONS.md). The knowledge graph model generalizes across asset types, plants, and document
formats without a schema change.

## Explainable AI with citations

Every copilot answer carries its supporting citations, a confidence score, and the specific
entities and documents it's grounded in — the "why this answer" panel exposes the retrieved
evidence in plain English. This is what separates a judgeable product from a scripted chatbot
demo.
