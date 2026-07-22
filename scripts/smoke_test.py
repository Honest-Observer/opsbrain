"""End-to-end smoke test for the OpsBrain demo path.

Exercises the exact sequence in MASTER_SPEC.md §11 against a LIVE backend
(no test client, no mocks) so we catch anything a unit test would miss:
seed -> ingestion status -> assets -> copilot ask (P-101) -> asset 360 ->
graph neighborhood -> compliance gaps -> lessons learned -> eval run.

Usage:
    python scripts/smoke_test.py [base_url]

Defaults to http://localhost:8000/api. The backend must already be running
(e.g. `uvicorn app.main:app --port 8000` from services/api). Exits non-zero
on the first failed assertion so it's CI/pre-demo-check friendly.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api"


def call(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        # Generous timeout: seeding + copilot answers are much slower when the
        # Gemini-powered RAG path is active (embeddings + LLM generation) than
        # in the local/offline mode.
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise AssertionError(f"{method} {path} -> HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}")


def step(name: str, fn):
    start = time.time()
    try:
        result = fn()
        print(f"[PASS] {name} ({(time.time() - start) * 1000:.0f}ms)")
        return result
    except Exception as e:  # noqa: BLE001 - smoke test, want any failure to abort loudly
        print(f"[FAIL] {name}: {e}")
        sys.exit(1)


def main() -> None:
    step("health check", lambda: assert_eq(call("GET", "/health")["status"], "ok"))

    seed = step("seed demo corpus", lambda: call("POST", "/ingestion/seed"))
    assert seed["documents_ingested"] >= 20, "expected >=20 seeded documents per MASTER_SPEC"

    status = step("ingestion status reflects seed", lambda: call("GET", "/ingestion/status"))
    assert_eq(status["documents"], seed["documents_ingested"])

    assets = step("list assets", lambda: call("GET", "/assets"))
    assert len(assets) > 0, "expected at least one seeded asset"
    p101 = next((a for a in assets if a["tag"] == "P-101"), None)
    assert p101 is not None, "demo story requires asset P-101 to exist"
    b12 = next((a for a in assets if a["tag"] == "B-12"), None)
    assert b12 is not None, "demo story requires asset B-12 to exist"

    answer = step(
        "copilot: why is P-101 repeatedly failing",
        lambda: call("POST", "/copilot/ask", {"question": "Why is Pump P-101 repeatedly failing?"}),
    )
    assert len(answer["citations"]) > 0, "copilot answer must include citations"
    assert 0 <= answer["confidence_score"] <= 1

    three60 = step("asset 360 for P-101", lambda: call("GET", f"/assets/{p101['id']}/three_sixty"))
    assert len(three60["recurring_issues"]) > 0, "P-101 demo story requires a recurring issue"

    graph = step(
        "graph neighborhood around P-101",
        lambda: call("GET", f"/graph/neighborhood?node_id={p101['id']}&depth=1"),
    )
    assert len(graph["nodes"]) > 0 and len(graph["edges"]) > 0

    gaps = step("compliance gaps", lambda: call("GET", "/compliance/gaps"))
    b12_gap = next((g for g in gaps if g["asset_tag"] == "B-12"), None)
    assert b12_gap is not None, "B-12 demo story requires a real compliance gap"

    step("evidence pack for B-12", lambda: call("GET", f"/compliance/evidence_pack/{b12['id']}"))

    lessons = step("lessons learned for P-101", lambda: call("GET", f"/lessons?asset_id={p101['id']}"))
    assert len(lessons) > 0, "P-101 demo story requires at least one lesson-learned match"

    eval_result = step("evaluation benchmark run", lambda: call("POST", "/eval/run"))
    assert eval_result["citation_coverage"] > 0

    print("\nAll demo-path smoke checks passed.")


def assert_eq(actual, expected):
    assert actual == expected, f"expected {expected!r}, got {actual!r}"
    return actual


if __name__ == "__main__":
    main()
