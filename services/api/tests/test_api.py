"""End-to-end API tests against a seeded DB (see conftest.py)."""
from __future__ import annotations

import io


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ingestion_seed_and_status(client):
    resp = client.post("/api/ingestion/seed")
    assert resp.status_code == 200
    body = resp.json()
    assert body["documents_ingested"] >= 20
    assert body["chunks_created"] >= 20
    assert body["entities_extracted"] > 0
    assert body["relationships_created"] > 0

    status = client.get("/api/ingestion/status").json()
    assert status["documents"] == body["documents_ingested"]
    assert status["chunks"] == body["chunks_created"]
    assert status["last_seeded_at"] is not None


def test_ingestion_upload(client):
    file_content = b"Pump P-101 upload smoke test mentioning WO-1041 and REG-022."
    resp = client.post(
        "/api/ingestion/upload",
        files={"file": ("upload_test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["document_id"]
    assert body["chunks_created"] >= 1


def test_list_documents(client):
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) > 0
    for field in ("id", "title", "doc_type", "source_path", "created_at"):
        assert field in docs[0]


def test_get_document_detail(client):
    doc_id = client.get("/api/documents").json()[0]["id"]
    resp = client.get(f"/api/documents/{doc_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == doc_id
    assert "chunks" in body
    assert len(body["chunks"]) >= 1


def test_get_document_404(client):
    resp = client.get("/api/documents/does-not-exist")
    assert resp.status_code == 404


def _find_asset(client, tag):
    assets = client.get("/api/assets").json()
    return next(a for a in assets if a["tag"] == tag)


def test_list_assets(client):
    assets = client.get("/api/assets").json()
    tags = {a["tag"] for a in assets}
    assert "P-101" in tags
    assert "B-12" in tags
    for field in ("id", "tag", "name", "asset_type", "criticality", "open_issues", "risk_score"):
        assert field in assets[0]


def test_asset_three_sixty_p101(client):
    p101 = _find_asset(client, "P-101")
    resp = client.get(f"/api/assets/{p101['id']}/three_sixty")
    assert resp.status_code == 200
    body = resp.json()
    assert body["asset"]["tag"] == "P-101"
    assert len(body["timeline"]) >= 3
    assert len(body["recurring_issues"]) >= 1
    assert body["recurring_issues"][0]["count"] >= 2
    assert len(body["similar_incidents"]) >= 1
    assert len(body["recommended_actions"]) >= 1


def test_asset_three_sixty_404(client):
    resp = client.get("/api/assets/does-not-exist/three_sixty")
    assert resp.status_code == 404


def test_search_semantic_p101(client):
    resp = client.get("/api/search/semantic", params={"q": "Why is Pump P-101 repeatedly failing?"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any("P-101" in r["text"] for r in results)
    for field in ("chunk_id", "document_id", "document_title", "text", "score"):
        assert field in results[0]


def test_graph_neighborhood_p101(client):
    p101 = _find_asset(client, "P-101")
    resp = client.get("/api/graph/neighborhood", params={"node_id": p101["id"], "depth": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) >= 1
    assert len(body["edges"]) >= 1


def test_copilot_ask_p101(client):
    resp = client.post("/api/copilot/ask", json={"question": "Why is Pump P-101 repeatedly failing?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "P-101" in body["answer"]
    assert 0.0 <= body["confidence_score"] <= 1.0
    assert len(body["citations"]) >= 1
    assert len(body["supporting_entities"]) >= 1
    assert len(body["recommended_actions"]) >= 1


def test_copilot_ask_compliance_question(client):
    resp = client.post("/api/copilot/ask", json={"question": "Show compliance gaps affecting Boiler B-12"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["citations"]) >= 1


def test_compliance_gaps(client):
    gaps = client.get("/api/compliance/gaps").json()
    assert len(gaps) >= 1
    b12_gap = next(g for g in gaps if g["asset_tag"] == "B-12")
    assert b12_gap["status"] == "gap"
    assert b12_gap["severity"] == "high"


def test_compliance_evidence_pack(client):
    b12 = _find_asset(client, "B-12")
    resp = client.get(f"/api/compliance/evidence_pack/{b12['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["asset_tag"] == "B-12"
    assert len(body["compliance_gaps"]) >= 1
    assert len(body["linked_documents"]) >= 1


def test_lessons_for_p101(client):
    p101 = _find_asset(client, "P-101")
    resp = client.get("/api/lessons", params={"asset_id": p101["id"]})
    assert resp.status_code == 200
    lessons = resp.json()
    assert len(lessons) >= 1
    assert "resembles" in lessons[0]["warning"].lower()


def test_eval_questions(client):
    questions = client.get("/api/eval/questions").json()
    assert len(questions) >= 20
    for field in ("id", "question", "expected_document_ids", "expected_entity_ids", "expects_citation"):
        assert field in questions[0]
    assert questions[0]["expects_citation"] is True


def test_eval_run(client):
    resp = client.post("/api/eval/run")
    assert resp.status_code == 200
    body = resp.json()
    for field in ("retrieval_hit_rate", "citation_coverage", "avg_latency_ms", "entity_linkage_coverage", "results"):
        assert field in body
    assert 0.0 <= body["retrieval_hit_rate"] <= 1.0
    assert 0.0 <= body["citation_coverage"] <= 1.0
    assert body["avg_latency_ms"] >= 0
    assert len(body["results"]) >= 20
