"""Core query/reasoning logic shared by the API routers.

Kept separate from the routers themselves so the HTTP layer (services/api/app/routers/*)
stays thin: parse request -> call a function here -> shape the response dict.
Nothing here talks HTTP; everything takes a `Session` and plain Python args.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from . import ingestion
from .corpus_generator import PEOPLE
from .db import vector_backend
from .embeddings import get_embedding_provider
from .models import (
    Asset,
    Chunk,
    ComplianceGap,
    Document,
    Entity,
    Incident,
    Inspection,
    Lesson,
    Recommendation,
    Regulation,
    Relationship,
    WorkOrder,
)


def entity_brief(ent: Entity) -> dict:
    return {"id": ent.id, "type": ent.entity_type, "label": ent.label}


# --------------------------------------------------------------------------
# Semantic search
# --------------------------------------------------------------------------

def semantic_search(db: Session, query: str, limit: int = 5) -> list[dict]:
    provider = get_embedding_provider()
    q_emb = provider.embed(query)
    results = vector_backend.search(db, q_emb, top_k=limit)
    out = []
    for chunk_id, score in results:
        chunk = db.get(Chunk, chunk_id)
        if chunk is None:
            continue
        doc = db.get(Document, chunk.document_id)
        out.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_title": doc.title if doc else "",
            "text": chunk.text,
            "score": round(score, 4),
        })
    return out


# --------------------------------------------------------------------------
# Graph neighborhood
# --------------------------------------------------------------------------

def _resolve_node_to_entity(db: Session, node_id: str) -> Entity | None:
    ent = db.get(Entity, node_id)
    if ent is not None:
        return ent
    asset = db.get(Asset, node_id)
    if asset is not None:
        from .seed import det_id
        return db.get(Entity, det_id("entity", "asset", asset.tag))
    doc = db.get(Document, node_id)
    if doc is not None:
        return db.query(Entity).filter(Entity.source_document_id == doc.id).first()
    return None


def graph_neighborhood(db: Session, node_id: str, depth: int = 1) -> dict:
    start = _resolve_node_to_entity(db, node_id)
    if start is None:
        return {"nodes": [], "edges": []}

    all_rels = db.query(Relationship).all()
    adjacency: dict[str, list[Relationship]] = defaultdict(list)
    for rel in all_rels:
        adjacency[rel.source_entity_id].append(rel)
        adjacency[rel.target_entity_id].append(rel)

    visited_ids = {start.id}
    frontier = [start.id]
    collected_edges: dict[str, Relationship] = {}

    for _ in range(max(depth, 0)):
        next_frontier = []
        for node in frontier:
            for rel in adjacency.get(node, []):
                collected_edges[rel.id] = rel
                other = rel.target_entity_id if rel.source_entity_id == node else rel.source_entity_id
                if other not in visited_ids:
                    visited_ids.add(other)
                    next_frontier.append(other)
        frontier = next_frontier
        if not frontier:
            break

    entities = db.query(Entity).filter(Entity.id.in_(visited_ids)).all()
    nodes = [{"id": e.id, "type": e.entity_type, "label": e.label} for e in entities]
    edges = [
        {
            "source": rel.source_entity_id,
            "target": rel.target_entity_id,
            "relationship_type": rel.relationship_type,
            "weight": rel.weight,
        }
        for rel in collected_edges.values()
    ]
    return {"nodes": nodes, "edges": edges}


# --------------------------------------------------------------------------
# Copilot ask
# --------------------------------------------------------------------------

def _entity_for_code(db: Session, entity_type: str, ref_code: str) -> Entity | None:
    from .seed import det_id
    return db.get(Entity, det_id("entity", entity_type, ref_code))


def copilot_ask(db: Session, question: str) -> dict:
    """Answer a free-form question.

    When Gemini is configured, this runs a real RAG pass (retrieve chunks ->
    ground a Gemini generation on them -> cite by source). If Gemini is off or
    the call fails, it falls back to the fully-offline deterministic path
    (`_copilot_ask_local`), so the endpoint never hard-fails.
    """
    from .config import gemini_enabled

    if gemini_enabled():
        try:
            return _copilot_ask_gemini(db, question)
        except Exception:
            # Any transient Gemini/network error -> graceful offline fallback.
            pass
    return _copilot_ask_local(db, question)


def _build_supporting_entities(db: Session, question: str, combined_text: str) -> list[dict]:
    question_entities = ingestion.extract_entities(question, PEOPLE)
    retrieved_entities = ingestion.extract_entities(combined_text, PEOPLE)
    supporting_entities: list[dict] = []
    seen_entity_ids: set[str] = set()
    for ex in question_entities + retrieved_entities:
        ent = _entity_for_code(db, ex.entity_type, ex.ref_code or ex.label)
        if ent is None or ent.id in seen_entity_ids:
            continue
        seen_entity_ids.add(ent.id)
        supporting_entities.append(entity_brief(ent))
    return supporting_entities


def _copilot_ask_gemini(db: Session, question: str) -> dict:
    """Real retrieval-augmented generation grounded in the ingested corpus."""
    from .gemini_client import generate_json

    provider = get_embedding_provider()
    q_emb = provider.embed(question)
    top = vector_backend.search(db, q_emb, top_k=12)

    retrieved: list[dict] = []
    combined_text_parts: list[str] = []
    for chunk_id, score in top:
        chunk = db.get(Chunk, chunk_id)
        if chunk is None:
            continue
        doc = db.get(Document, chunk.document_id)
        if doc is None:
            continue
        retrieved.append({
            "chunk": chunk, "doc": doc, "score": score,
        })
        combined_text_parts.append(chunk.text)

    if not retrieved:
        return {
            "answer": (
                "I couldn't find anything relevant in the current knowledge base. "
                "Seed the demo corpus or upload documents on the Ingest page, then ask again."
            ),
            "confidence_score": 0.0,
            "citations": [],
            "supporting_entities": [],
            "supporting_documents": [],
            "recommended_actions": [],
        }

    # Build a numbered context block the model must cite by index.
    # Show whole chunks (not tiny snippets): the earlier 900-char cap meant that
    # for row-heavy data like a CSV the model only saw the first few rows of each
    # chunk and couldn't answer aggregate questions ("how many..."). gemini-3.5
    # has a very large context window, so we give each chunk a generous per-chunk
    # limit and keep a total budget as a safety cap.
    PER_CHUNK_CHAR_LIMIT = 6000
    TOTAL_CONTEXT_CHAR_BUDGET = 60000
    context_blocks = []
    used = 0
    for i, r in enumerate(retrieved):
        snippet = r["chunk"].text.strip()
        if len(snippet) > PER_CHUNK_CHAR_LIMIT:
            snippet = snippet[:PER_CHUNK_CHAR_LIMIT] + "..."
        block = f"[{i}] ({r['doc'].doc_type}) {r['doc'].title}\n{snippet}"
        if context_blocks and used + len(block) > TOTAL_CONTEXT_CHAR_BUDGET:
            break
        context_blocks.append(block)
        used += len(block)
    context = "\n\n".join(context_blocks)

    prompt = (
        "You are OpsBrain, an industrial knowledge assistant for plant engineers, "
        "maintenance leads, and auditors. Answer the user's question using ONLY the "
        "numbered CONTEXT below (retrieved from the plant's ingested documents). "
        "Ground every claim in the context and cite the numbered sources you used by their "
        "indices. If the context is insufficient, say so honestly and set a low confidence. "
        "Be specific and operational: name assets, failure modes, work orders, incidents, and "
        "regulations where relevant, and give concrete recommended actions. "
        "Write the answer as clear plain prose (short paragraphs); do NOT use markdown "
        "headings, bold, or bullet syntax in the 'answer' field.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Respond as JSON matching the provided schema. 'cited_chunk_indices' must be a subset "
        "of the indices shown in brackets above. 'confidence' is 0..1 reflecting how well the "
        "context supports your answer."
    )

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"},
            "cited_chunk_indices": {"type": "array", "items": {"type": "integer"}},
            "recommended_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "rationale": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                    "required": ["action", "rationale", "priority"],
                },
            },
        },
        "required": ["answer", "confidence", "cited_chunk_indices"],
    }

    result = generate_json(prompt, schema, max_output_tokens=8192)

    answer = str(result.get("answer", "")).strip()
    model_conf = float(result.get("confidence", 0.5) or 0.5)
    cited_idx = result.get("cited_chunk_indices") or []

    citations = []
    supporting_docs: dict[str, dict] = {}
    valid_indices = [i for i in cited_idx if isinstance(i, int) and 0 <= i < len(retrieved)]
    # If the model cited nothing valid, fall back to citing the top-2 retrieved.
    if not valid_indices:
        valid_indices = list(range(min(2, len(retrieved))))
    for i in valid_indices:
        r = retrieved[i]
        snippet = r["chunk"].text.strip()
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."
        citations.append({
            "document_id": r["doc"].id,
            "document_title": r["doc"].title,
            "chunk_id": r["chunk"].id,
            "snippet": snippet,
        })
        supporting_docs[r["doc"].id] = {"id": r["doc"].id, "title": r["doc"].title}

    recommended_actions = []
    for ra in (result.get("recommended_actions") or []):
        if not isinstance(ra, dict):
            continue
        recommended_actions.append({
            "action": str(ra.get("action", "")).strip(),
            "rationale": str(ra.get("rationale", "")).strip(),
            "priority": ra.get("priority", "medium") if ra.get("priority") in ("low", "medium", "high") else "medium",
        })

    supporting_entities = _build_supporting_entities(db, question, " ".join(combined_text_parts))

    best_score = retrieved[0]["score"] if retrieved else 0.0
    retrieval_norm = max(0.0, min(1.0, (best_score + 1) / 2))
    confidence_score = round(max(0.0, min(1.0, 0.5 * model_conf + 0.5 * retrieval_norm)), 2)

    return {
        "answer": answer,
        "confidence_score": confidence_score,
        "citations": citations,
        "supporting_entities": supporting_entities,
        "supporting_documents": list(supporting_docs.values()),
        "recommended_actions": recommended_actions,
    }


def _copilot_ask_local(db: Session, question: str) -> dict:
    provider = get_embedding_provider()
    q_emb = provider.embed(question)
    top = vector_backend.search(db, q_emb, top_k=5)

    citations = []
    supporting_docs: dict[str, dict] = {}
    combined_text_parts: list[str] = []
    best_score = top[0][1] if top else 0.0

    for chunk_id, score in top:
        chunk = db.get(Chunk, chunk_id)
        if chunk is None:
            continue
        doc = db.get(Document, chunk.document_id)
        if doc is None:
            continue
        snippet = chunk.text.strip()
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."
        citations.append({
            "document_id": doc.id,
            "document_title": doc.title,
            "chunk_id": chunk.id,
            "snippet": snippet,
        })
        supporting_docs[doc.id] = {"id": doc.id, "title": doc.title}
        combined_text_parts.append(chunk.text)

    # entity extraction over the question + retrieved text to find focus entities
    question_entities = ingestion.extract_entities(question, PEOPLE)
    retrieved_entities = ingestion.extract_entities(" ".join(combined_text_parts), PEOPLE)

    supporting_entities: list[dict] = []
    seen_entity_ids: set[str] = set()

    def add_supporting(entity_type: str, ref_code: str | None, label: str):
        ent = _entity_for_code(db, entity_type, ref_code or label)
        if ent is None:
            return
        if ent.id in seen_entity_ids:
            return
        seen_entity_ids.add(ent.id)
        supporting_entities.append(entity_brief(ent))

    for ex in question_entities + retrieved_entities:
        add_supporting(ex.entity_type, ex.ref_code, ex.label)

    # Identify a single focus asset (if any) to ground the templated answer
    focus_asset: Asset | None = None
    asset_codes = [e.ref_code for e in question_entities if e.entity_type == "asset"]
    if not asset_codes:
        asset_codes = [e.ref_code for e in retrieved_entities if e.entity_type == "asset"]
    if asset_codes:
        focus_asset = db.query(Asset).filter(Asset.tag == asset_codes[0]).first()

    recommended_actions: list[dict] = []
    answer_parts: list[str] = []

    if focus_asset is not None:
        work_orders = (
            db.query(WorkOrder)
            .filter(WorkOrder.asset_id == focus_asset.id)
            .order_by(WorkOrder.opened_at)
            .all()
        )
        incidents = (
            db.query(Incident)
            .filter(Incident.asset_id == focus_asset.id)
            .order_by(Incident.occurred_at)
            .all()
        )
        gaps = (
            db.query(ComplianceGap)
            .filter(ComplianceGap.asset_id == focus_asset.id, ComplianceGap.status != "ok")
            .all()
        )

        failure_counts: dict[str, list[WorkOrder]] = defaultdict(list)
        for wo in work_orders:
            if wo.failure_mode:
                failure_counts[wo.failure_mode].append(wo)

        answer_parts.append(
            f"{focus_asset.name} ({focus_asset.tag}) is a {focus_asset.criticality}-criticality "
            f"{focus_asset.asset_type} at {focus_asset.location}."
        )

        recurring = {fm: wos for fm, wos in failure_counts.items() if len(wos) >= 2}
        if recurring:
            for fm, wos in recurring.items():
                wo_numbers = ", ".join(w.wo_number for w in wos)
                last = max(wos, key=lambda w: w.opened_at)
                answer_parts.append(
                    f"It has a recurring failure pattern: '{fm}' recorded across {len(wos)} work "
                    f"orders ({wo_numbers}), most recently opened {last.opened_at.date().isoformat()}."
                )
        elif work_orders:
            answer_parts.append(
                f"It has {len(work_orders)} maintenance work order(s) on record "
                f"({', '.join(w.wo_number for w in work_orders)})."
            )

        if incidents:
            inc_desc = "; ".join(f"{i.incident_code} ({i.title})" for i in incidents)
            answer_parts.append(f"Related incident history: {inc_desc}.")

        if gaps:
            gap_desc = "; ".join(g.checklist_item for g in gaps)
            answer_parts.append(
                f"There is an open compliance gap: {gap_desc}. See citations and compliance "
                f"board for evidence detail."
            )

        recs = db.query(Recommendation).filter(Recommendation.asset_id == focus_asset.id).all()
        for r in recs:
            recommended_actions.append({"action": r.action, "rationale": r.rationale, "priority": r.priority})

        if not recommended_actions and recurring:
            recommended_actions.append({
                "action": f"Investigate root cause of recurring '{next(iter(recurring))}' on {focus_asset.tag}.",
                "rationale": "Repeated failures of the same mode indicate an unresolved root cause rather than routine wear.",
                "priority": "high",
            })
    else:
        if citations:
            top_titles = ", ".join(sorted({c["document_title"] for c in citations}))
            answer_parts.append(
                f"Based on the most relevant records found ({top_titles}), here is what the "
                f"knowledge base shows:"
            )
            answer_parts.append(citations[0]["snippet"])
        else:
            answer_parts.append(
                "No closely matching documents were found for this question in the current "
                "knowledge base. Try rephrasing with an asset tag, work order number, or "
                "incident code."
            )

    answer = " ".join(answer_parts)

    # Confidence: blend of top retrieval score and citation depth, clamped to [0, 1].
    normalized_score = max(0.0, min(1.0, (best_score + 1) / 2))  # cosine in [-1,1] -> [0,1]
    citation_factor = min(len(citations), 3) / 3
    confidence_score = round(0.6 * normalized_score + 0.4 * citation_factor, 2)

    return {
        "answer": answer,
        "confidence_score": confidence_score,
        "citations": citations,
        "supporting_entities": supporting_entities,
        "supporting_documents": list(supporting_docs.values()),
        "recommended_actions": recommended_actions,
    }


# --------------------------------------------------------------------------
# Asset 360
# --------------------------------------------------------------------------

def asset_three_sixty(db: Session, asset_id: str) -> dict | None:
    asset = db.get(Asset, asset_id)
    if asset is None:
        return None

    work_orders = db.query(WorkOrder).filter(WorkOrder.asset_id == asset.id).all()
    incidents = db.query(Incident).filter(Incident.asset_id == asset.id).all()
    inspections = db.query(Inspection).filter(Inspection.asset_id == asset.id).all()

    timeline = []
    for wo in work_orders:
        timeline.append({
            "date": wo.opened_at.date().isoformat(),
            "type": "work_order",
            "title": wo.description[:80],
            "ref_id": wo.wo_number,
            "summary": wo.description,
        })
    for inc in incidents:
        timeline.append({
            "date": inc.occurred_at.date().isoformat(),
            "type": "incident",
            "title": inc.title,
            "ref_id": inc.incident_code,
            "summary": inc.summary,
        })
    for insp in inspections:
        timeline.append({
            "date": insp.inspected_at.date().isoformat(),
            "type": "inspection",
            "title": insp.checklist_item,
            "ref_id": insp.id,
            "summary": f"Result: {insp.result} (inspector: {insp.inspector})",
        })
    timeline.sort(key=lambda t: t["date"])

    failure_counts: dict[str, list[WorkOrder]] = defaultdict(list)
    for wo in work_orders:
        if wo.failure_mode:
            failure_counts[wo.failure_mode].append(wo)
    recurring_issues = [
        {
            "failure_mode": fm,
            "count": len(wos),
            "last_seen": max(w.opened_at for w in wos).date().isoformat(),
        }
        for fm, wos in failure_counts.items()
    ]

    incident_ids = {i.id for i in incidents}
    lessons = (
        db.query(Lesson)
        .filter((Lesson.incident_id.in_(incident_ids)) | (Lesson.similar_incident_id.in_(incident_ids)))
        .all()
        if incident_ids
        else []
    )
    similar_incidents = []
    seen_pairs = set()
    for lesson in lessons:
        other_id = lesson.similar_incident_id if lesson.incident_id in incident_ids else lesson.incident_id
        if other_id in seen_pairs:
            continue
        seen_pairs.add(other_id)
        other = db.get(Incident, other_id)
        if other is None:
            continue
        similar_incidents.append({
            "incident_id": other.incident_code,
            "title": other.title,
            "similarity": lesson.similarity,
            "summary": other.summary,
        })

    gaps = db.query(ComplianceGap).filter(ComplianceGap.asset_id == asset.id).all()
    compliance_issues = [
        {"checklist_item": g.checklist_item, "status": g.status, "severity": g.severity}
        for g in gaps
    ]

    recs = db.query(Recommendation).filter(Recommendation.asset_id == asset.id).all()
    recommended_actions = [
        {"action": r.action, "rationale": r.rationale, "priority": r.priority} for r in recs
    ]

    from .seed import det_id
    asset_entity = db.get(Entity, det_id("entity", "asset", asset.tag))
    linked_documents = []
    if asset_entity is not None:
        rels = (
            db.query(Relationship)
            .filter(
                Relationship.source_entity_id == asset_entity.id,
                Relationship.relationship_type.in_(["asset->document", "asset->procedure"]),
            )
            .all()
        )
        for rel in rels:
            target = db.get(Entity, rel.target_entity_id)
            if target is None or target.source_document_id is None:
                continue
            doc = db.get(Document, target.source_document_id)
            if doc is None:
                continue
            linked_documents.append({"id": doc.id, "title": doc.title, "doc_type": doc.doc_type})

    return {
        "asset": {
            "id": asset.id,
            "tag": asset.tag,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "criticality": asset.criticality,
            "location": asset.location,
        },
        "timeline": timeline,
        "recurring_issues": recurring_issues,
        "similar_incidents": similar_incidents,
        "compliance_issues": compliance_issues,
        "recommended_actions": recommended_actions,
        "linked_documents": linked_documents,
    }


# --------------------------------------------------------------------------
# Compliance
# --------------------------------------------------------------------------

def compliance_gaps_list(db: Session) -> list[dict]:
    gaps = db.query(ComplianceGap).all()
    out = []
    for g in gaps:
        asset = db.get(Asset, g.asset_id) if g.asset_id else None
        reg = db.get(Regulation, g.regulation_id) if g.regulation_id else None
        out.append({
            "id": g.id,
            "asset_tag": asset.tag if asset else None,
            "checklist_item": g.checklist_item,
            "regulation_ref": reg.code if reg else None,
            "status": g.status,
            "severity": g.severity,
            "missing_evidence": g.missing_evidence,
            "corrective_action": g.corrective_action,
        })
    return out


def evidence_pack(db: Session, asset_id: str) -> dict | None:
    asset = db.get(Asset, asset_id)
    if asset is None:
        return None

    gaps = compliance_gaps_list(db)
    asset_gaps = [g for g in gaps if g["asset_tag"] == asset.tag]

    from .seed import det_id
    asset_entity = db.get(Entity, det_id("entity", "asset", asset.tag))
    linked_documents = []
    supporting_entities = []
    if asset_entity is not None:
        rels = (
            db.query(Relationship)
            .filter(Relationship.source_entity_id == asset_entity.id)
            .all()
        )
        for rel in rels:
            target = db.get(Entity, rel.target_entity_id)
            if target is None:
                continue
            supporting_entities.append({
                "id": target.id, "type": target.entity_type, "label": target.label,
                "ref_code": target.ref_code,
            })
            if target.source_document_id:
                doc = db.get(Document, target.source_document_id)
                if doc is not None:
                    linked_documents.append({
                        "id": doc.id, "title": doc.title, "doc_type": doc.doc_type,
                        "source_path": doc.source_path,
                    })

    # de-dup linked_documents by id
    seen = set()
    deduped_docs = []
    for d in linked_documents:
        if d["id"] in seen:
            continue
        seen.add(d["id"])
        deduped_docs.append(d)

    return {
        "asset_id": asset.id,
        "asset_tag": asset.tag,
        "asset_name": asset.name,
        "generated_at": datetime.utcnow().isoformat(),
        "compliance_gaps": asset_gaps,
        "linked_documents": deduped_docs,
        "supporting_entities": supporting_entities,
    }


# --------------------------------------------------------------------------
# Lessons learned
# --------------------------------------------------------------------------

def lessons_for_asset(db: Session, asset_id: str | None) -> list[dict]:
    query = db.query(Incident)
    if asset_id:
        query = query.filter(Incident.asset_id == asset_id)
    incidents = query.all()
    incident_ids = {i.id for i in incidents}
    if not incident_ids:
        return []

    lessons = db.query(Lesson).filter(Lesson.incident_id.in_(incident_ids)).all()
    out = []
    for lesson in lessons:
        similar = db.get(Incident, lesson.similar_incident_id)
        if similar is None:
            continue
        out.append({
            "incident_id": similar.incident_code,
            "title": similar.title,
            "summary": similar.summary,
            "similarity": lesson.similarity,
            "date": similar.occurred_at.date().isoformat(),
            "warning": lesson.warning_text,
        })
    return out
