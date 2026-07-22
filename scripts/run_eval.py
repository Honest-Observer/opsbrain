#!/usr/bin/env python
"""CLI wrapper for the OpsBrain evaluation harness (MASTER_SPEC §10).

Usage (from repo root, after installing services/api/requirements.txt):

    python scripts/run_eval.py

Prints the same JSON shape returned by `POST /api/eval/run`:
    { retrieval_hit_rate, citation_coverage, avg_latency_ms,
      entity_linkage_coverage, results: [...] }

The actual computation lives in `services/api/app/eval_engine.py` so both
this CLI and the HTTP endpoint stay in sync; this script just wires up
sys.path + a DB session and prints the result.
"""
from __future__ import annotations

import json
import os
import sys

API_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services", "api")
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

from app.db import SessionLocal, init_db  # noqa: E402
from app.eval_engine import run_evaluation  # noqa: E402
from app.models import Document  # noqa: E402
from app.seed import run_seed  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Document).count() == 0:
            print("No documents found in DB yet -- seeding from the sample corpus first...", file=sys.stderr)
            run_seed(db)
        result = run_evaluation(db)
    finally:
        db.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
