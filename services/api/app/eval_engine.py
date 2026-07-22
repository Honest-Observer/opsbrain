"""Evaluation harness (MASTER_SPEC §10).

Computes the four benchmark metrics against `data/eval/questions.json`
(seeded into the `benchmark_questions` table by `seed.run_seed`, with a
direct file-read fallback so `GET /eval/questions` / `POST /eval/run` work
even before the first seed). This module contains the actual logic; both
`scripts/run_eval.py` (CLI) and `POST /api/eval/run` call `run_evaluation`.
"""
from __future__ import annotations

import json
import os
import time

from sqlalchemy.orm import Session

from . import reasoning
from .models import BenchmarkQuestion

QUESTIONS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "eval",
    "questions.json",
)


def _load_questions(db: Session) -> list[dict]:
    rows = db.query(BenchmarkQuestion).all()
    if rows:
        return [
            {
                "id": q.id,
                "question": q.question,
                "expected_document_ids": json.loads(q.expected_document_ids),
                "expected_entity_ids": json.loads(q.expected_entity_ids),
                "expects_citation": q.expects_citation,
            }
            for q in rows
        ]
    if os.path.exists(QUESTIONS_PATH):
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return []


def run_evaluation(db: Session) -> dict:
    questions = _load_questions(db)
    results = []
    retrieval_hits: list[bool] = []
    citation_hits: list[bool] = []
    entity_linkage_fractions: list[float] = []
    latencies: list[float] = []

    for q in questions:
        expected_docs = set(q.get("expected_document_ids", []))
        expected_entities = set(q.get("expected_entity_ids", []))

        # Use the deterministic local answer composer for scoring even when
        # Gemini is enabled: it still retrieves over the real (Gemini) embeddings
        # but composes citations/entities instantly, so a full benchmark run
        # stays fast, reproducible, and free of 24 LLM generation calls. The
        # metrics here measure the retrieval + grounding system, which is what
        # a benchmark should hold stable — not the phrasing of the LLM prose.
        t0 = time.perf_counter()
        answer = reasoning._copilot_ask_local(db, q["question"])
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        top_docs = reasoning.semantic_search(db, q["question"], limit=5)
        top_doc_ids = {r["document_id"] for r in top_docs}
        retrieval_hit = True if not expected_docs else bool(expected_docs & top_doc_ids)
        retrieval_hits.append(retrieval_hit)

        citation_ok = len(answer["citations"]) >= 1
        citation_hits.append(citation_ok)

        supporting_ids = {e["id"] for e in answer["supporting_entities"]}
        if expected_entities:
            fraction = len(expected_entities & supporting_ids) / len(expected_entities)
        else:
            fraction = 1.0
        entity_linkage_fractions.append(fraction)

        passed = retrieval_hit and citation_ok
        results.append({
            "question_id": q["id"],
            "passed": passed,
            "latency_ms": round(latency_ms, 2),
        })

    def _mean(values: list[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    return {
        "retrieval_hit_rate": _mean([1.0 if h else 0.0 for h in retrieval_hits]),
        "citation_coverage": _mean([1.0 if h else 0.0 for h in citation_hits]),
        "avg_latency_ms": round(_mean(latencies), 2),
        "entity_linkage_coverage": _mean(entity_linkage_fractions),
        "results": results,
    }
