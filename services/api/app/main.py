"""OpsBrain FastAPI entrypoint.

Implements the full frozen API contract from MASTER_SPEC.md §6. All routes
are mounted under `/api` to match `Base URL: http://localhost:8000/api`.
Every endpoint works with zero external API keys / zero network access —
retrieval, extraction, and answer synthesis are all local/deterministic
(ADR-007, ADR-008).
"""
from __future__ import annotations

import json
import os
import shutil
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import reasoning
from .corpus_generator import PEOPLE
from .db import get_db, init_db, vector_backend
from .embeddings import get_embedding_provider
from .ingestion import chunk_text, extract_entities, parse_file
from .models import (
    Asset,
    BenchmarkQuestion,
    Chunk,
    ComplianceGap,
    Document,
    Entity,
    IngestionRun,
    Relationship,
    WorkOrder,
)
from .seed import det_id, run_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="OpsBrain API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# CORS-safe error handling
# ---------------------------------------------------------------------------
# Starlette's ServerErrorMiddleware sits OUTSIDE CORSMiddleware, so an
# unhandled exception returns a 500 with NO CORS headers — which a browser
# reports misleadingly as "No 'Access-Control-Allow-Origin' header" instead of
# the real error. This handler catches any unhandled exception and returns a
# JSON error WITH permissive CORS headers, so the frontend always sees the
# actual message (and the app never appears to fail for "CORS" reasons).
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.requests import Request  # noqa: E402


import logging  # noqa: E402
import traceback as _traceback  # noqa: E402

_logger = logging.getLogger("opsbrain")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log the full traceback server-side (a custom Exception handler otherwise
    # swallows it), and return the concise message to the client WITH CORS
    # headers so it's never masked as a CORS failure.
    _logger.error("Unhandled error on %s %s:\n%s", request.method, request.url.path,
                  "".join(_traceback.format_exception(type(exc), exc, exc.__traceback__)))
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
        headers={"Access-Control-Allow-Origin": "*"},
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    from .config import ai_mode, ai_model_label, gemini_enabled

    return {
        "status": "ok",
        "version": app.version,
        "ai_mode": ai_mode(),          # "gemini" | "local"
        "ai_model": ai_model_label(),
        "gemini_enabled": gemini_enabled(),
    }


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

@app.post("/api/ingestion/seed")
def ingestion_seed(db: Session = Depends(get_db)):
    return run_seed(db)


@app.get("/api/ingestion/status")
def ingestion_status(db: Session = Depends(get_db)):
    last_run = db.query(IngestionRun).order_by(IngestionRun.seeded_at.desc()).first()
    return {
        "documents": db.query(Document).count(),
        "chunks": db.query(Chunk).count(),
        "entities": db.query(Entity).count(),
        "relationships": db.query(Relationship).count(),
        "last_seeded_at": last_run.seeded_at.isoformat() if last_run else None,
    }


# Cap how many chunks we embed on a single upload so a very large file can't
# hang the request or blow through embedding rate limits. Chunks beyond the cap
# are still stored (and graph-extracted); they just aren't in the vector index.
MAX_EMBED_CHUNKS_PER_UPLOAD = 60
# Cap how many LLM-extracted entities a single upload applies, so a huge/row-heavy
# file (e.g. a CSV where the model emits one entity per row) can't bloat the graph
# or the transaction.
MAX_LLM_ENTITIES_PER_UPLOAD = 80


# NOTE: sync `def` (not `async def`) on purpose. This handler does blocking work
# (file I/O + synchronous Gemini HTTP calls); FastAPI runs sync endpoints in a
# worker thread, so it never blocks the event loop. As an async def it would
# stall the whole server for the duration of the upload.
@app.post("/api/ingestion/upload")
def ingestion_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
        "uploads",
    )
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = os.path.basename(file.filename or "upload.txt")
    dest_path = os.path.join(upload_dir, safe_name)
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        parsed = parse_file(dest_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse '{safe_name}': {exc}")

    text = parsed.text
    doc_type = parsed.metadata.get("doc_type", "document")
    title = parsed.metadata.get("title", safe_name)
    source_path = os.path.relpath(dest_path, os.path.dirname(upload_dir)).replace("\\", "/")

    doc = Document(
        id=det_id("document", source_path, str(time.time())),
        title=title,
        doc_type=doc_type,
        source_path=source_path,
        raw_text=text,
    )
    db.add(doc)
    db.flush()

    provider = get_embedding_provider()
    chunks_created = 0
    chunks_embedded = 0
    embed_errors = 0
    for idx, chunk_val, start, end in chunk_text(text):
        chunk = Chunk(
            document_id=doc.id,
            chunk_index=idx,
            text=chunk_val,
            char_start=start,
            char_end=end,
            embedding="[]",
        )
        db.add(chunk)
        db.flush()
        # Resilient, bounded embedding: a single embedding failure (e.g. a
        # transient Gemini rate-limit) must not abort the whole upload. The
        # chunk is still stored; it just won't be semantically searchable.
        if chunks_embedded < MAX_EMBED_CHUNKS_PER_UPLOAD:
            try:
                vector_backend.upsert(db, chunk.id, provider.embed(chunk_val))
                chunks_embedded += 1
            except Exception:
                embed_errors += 1
        chunks_created += 1

    # Best-effort entity extraction + linking to a fresh document-level
    # entity. This is a lighter-weight path than the full structured graph
    # builder in seed.py (which also updates operational tables), suitable
    # for a single ad hoc upload.
    doc_entity_type = "procedure" if doc_type == "sop" else ("inspection" if doc_type == "inspection" else "document")
    doc_entity_id = det_id("entity", doc_entity_type, title)
    doc_entity = db.get(Entity, doc_entity_id)
    if doc_entity is None:
        doc_entity = Entity(id=doc_entity_id, entity_type=doc_entity_type, label=title,
                             ref_code=None, source_document_id=doc.id)
        db.add(doc_entity)
        db.flush()

    entities_created = 0
    relationships_created = 0
    label_to_entity_id: dict[str, str] = {}

    for ex in extract_entities(text, PEOPLE):
        ent_id = det_id("entity", ex.entity_type, ex.ref_code or ex.label)
        ent = db.get(Entity, ent_id)
        if ent is None:
            ent = Entity(id=ent_id, entity_type=ex.entity_type, label=ex.label,
                         ref_code=ex.ref_code, source_document_id=doc.id)
            db.add(ent)
            db.flush()
            entities_created += 1
        label_to_entity_id[ex.label] = ent.id
        if ex.ref_code:
            label_to_entity_id[ex.ref_code] = ent.id
        if ex.entity_type == "asset":
            edge_type = "asset->procedure" if doc_type == "sop" else "asset->document"
            db.add(Relationship(source_entity_id=ent.id, target_entity_id=doc_entity.id,
                                 relationship_type=edge_type, weight=1.0))
            relationships_created += 1

    # PHASE 1 COMMIT: the document is now parsed, chunked, embedded, and
    # regex-linked. Commit here so the upload is guaranteed to succeed and be
    # queryable even if the optional LLM graph step below fails.
    db.commit()

    # PHASE 2 (best-effort): LLM-based graph extraction for arbitrary uploaded
    # content (Gemini only). This is what lets OpsBrain "learn" raw data beyond
    # the fixed regex code patterns. Bounded + fully error-contained: any
    # failure here rolls back only this phase and never fails the upload.
    from .extraction_llm import extract_graph

    core_entities, core_relationships = entities_created, relationships_created
    llm_applied = False
    try:
        llm_graph = extract_graph(text)
        if llm_graph:
            seen_entity_ids: set[str] = set()
            for e in llm_graph["entities"][:MAX_LLM_ENTITIES_PER_UPLOAD]:
                key = e["ref_code"] or e["label"]
                ent_id = det_id("entity", e["entity_type"], key)
                if ent_id in seen_entity_ids:
                    continue
                seen_entity_ids.add(ent_id)
                ent = db.get(Entity, ent_id)
                if ent is None:
                    ent = Entity(id=ent_id, entity_type=e["entity_type"], label=e["label"],
                                 ref_code=e["ref_code"], source_document_id=doc.id)
                    db.add(ent)
                    db.flush()
                    entities_created += 1
                label_to_entity_id[e["label"]] = ent.id
                if e["ref_code"]:
                    label_to_entity_id[e["ref_code"]] = ent.id
                # Link each extracted entity to this document (once) so it shows
                # up in the graph.
                db.add(Relationship(source_entity_id=ent.id, target_entity_id=doc_entity.id,
                                     relationship_type="asset->document", weight=0.8))
                relationships_created += 1
            for r in llm_graph["relationships"]:
                src = label_to_entity_id.get(r["source_label"])
                tgt = label_to_entity_id.get(r["target_label"])
                if src and tgt and src != tgt:
                    db.add(Relationship(source_entity_id=src, target_entity_id=tgt,
                                         relationship_type=r["relationship_type"], weight=1.0))
                    relationships_created += 1
            db.commit()
            llm_applied = True
    except Exception:
        # LLM graph step failed (bad payload, rate limit, DB constraint, ...).
        # Roll back just this phase; the core ingestion (phase 1) already stands.
        db.rollback()
        entities_created, relationships_created = core_entities, core_relationships
        _logger.exception("LLM graph extraction failed for upload %s; core ingestion kept.", doc.id)

    from .config import ai_mode

    return {
        "document_id": doc.id,
        "chunks_created": chunks_created,
        "chunks_embedded": chunks_embedded,
        "embed_errors": embed_errors,
        "entities_created": entities_created,
        "relationships_created": relationships_created,
        "graph_extracted": llm_applied,
        "ai_mode": ai_mode(),
    }


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@app.get("/api/documents")
def list_documents(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                    db: Session = Depends(get_db)):
    docs = (
        db.query(Document)
        .order_by(Document.created_at)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": d.id,
            "title": d.title,
            "doc_type": d.doc_type,
            "source_path": d.source_path,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@app.get("/api/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == doc.id)
        .order_by(Chunk.chunk_index)
        .all()
    )
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "source_path": doc.source_path,
        "raw_text": doc.raw_text,
        "created_at": doc.created_at.isoformat(),
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "text": c.text,
                "char_start": c.char_start,
                "char_end": c.char_end,
            }
            for c in chunks
        ],
    }


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

@app.get("/api/assets")
def list_assets(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                 db: Session = Depends(get_db)):
    assets = db.query(Asset).order_by(Asset.tag).offset(offset).limit(limit).all()
    out = []
    for a in assets:
        open_wo = db.query(WorkOrder).filter(WorkOrder.asset_id == a.id, WorkOrder.status == "open").count()
        open_gaps = db.query(ComplianceGap).filter(ComplianceGap.asset_id == a.id, ComplianceGap.status != "ok").count()
        out.append({
            "id": a.id,
            "tag": a.tag,
            "name": a.name,
            "asset_type": a.asset_type,
            "criticality": a.criticality,
            "open_issues": open_wo + open_gaps,
            "risk_score": a.risk_score,
        })
    return out


@app.get("/api/assets/{asset_id}/three_sixty")
def get_asset_three_sixty(asset_id: str, db: Session = Depends(get_db)):
    result = reasoning.asset_three_sixty(db, asset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return result


# ---------------------------------------------------------------------------
# Search / Reasoning
# ---------------------------------------------------------------------------

@app.get("/api/search/semantic")
def search_semantic(q: str, limit: int = Query(5, ge=1, le=50), offset: int = Query(0, ge=0),
                     db: Session = Depends(get_db)):
    results = reasoning.semantic_search(db, q, limit=limit + offset)
    return results[offset: offset + limit]


@app.get("/api/graph/neighborhood")
def graph_neighborhood(node_id: str, depth: int = Query(1, ge=0, le=5),
                        db: Session = Depends(get_db)):
    return reasoning.graph_neighborhood(db, node_id, depth=depth)


class CopilotAskRequest(BaseModel):
    question: str


@app.post("/api/copilot/ask")
def copilot_ask(payload: CopilotAskRequest, db: Session = Depends(get_db)):
    return reasoning.copilot_ask(db, payload.question)


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

@app.get("/api/compliance/gaps")
def compliance_gaps(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                     db: Session = Depends(get_db)):
    gaps = reasoning.compliance_gaps_list(db)
    return gaps[offset: offset + limit]


@app.get("/api/compliance/evidence_pack/{asset_id}")
def compliance_evidence_pack(asset_id: str, db: Session = Depends(get_db)):
    result = reasoning.evidence_pack(db, asset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return result


# ---------------------------------------------------------------------------
# Lessons learned
# ---------------------------------------------------------------------------

@app.get("/api/lessons")
def lessons(asset_id: str | None = None, limit: int = Query(50, ge=1, le=500),
            offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    result = reasoning.lessons_for_asset(db, asset_id)
    return result[offset: offset + limit]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@app.get("/api/eval/questions")
def eval_questions(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0),
                    db: Session = Depends(get_db)):
    rows = db.query(BenchmarkQuestion).offset(offset).limit(limit).all()
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
    # Fallback: DB not seeded yet, read straight from the benchmark file.
    from .eval_engine import QUESTIONS_PATH

    if not os.path.exists(QUESTIONS_PATH):
        return []
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as fh:
        questions = json.load(fh)
    return questions[offset: offset + limit]


@app.post("/api/eval/run")
def eval_run(db: Session = Depends(get_db)):
    from .eval_engine import run_evaluation

    return run_evaluation(db)
