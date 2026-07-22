"""Seeds the DB from the synthetic corpus (MASTER_SPEC §8, §11 demo flow).

Two layers of data are populated, both derived from the same
`corpus_generator` constants so they are guaranteed internally consistent:

1. **Structured operational tables** (assets, regulations, work_orders,
   incidents, inspections, compliance_gaps) — seeded directly from the
   generator's canonical Python data, mirroring how these facts would come
   from a real CMMS/EAM system rather than being re-parsed out of prose.
2. **Documents / chunks / entities / relationships** — produced by actually
   running the ingestion pipeline (`ingestion.py`) over every generated
   file on disk, so the search/graph/copilot layers are exercised against
   real parsed-and-chunked-and-regex-extracted content, per ADR-007.

`run_seed(db)` is idempotent: it wipes and reloads all tables so
`POST /ingestion/seed` can be called repeatedly during a demo.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from . import ingestion
from .corpus_generator import (
    ASSETS,
    COMPLIANCE_GAP,
    INCIDENTS,
    INSPECTIONS,
    PEOPLE,
    REGULATIONS,
    WORK_ORDERS,
    generate_corpus,
)
from .db import vector_backend
from .embeddings import get_embedding_provider
from .models import (
    Asset,
    BenchmarkQuestion,
    Chunk,
    ComplianceGap,
    Document,
    Entity,
    Incident,
    Inspection,
    IngestionRun,
    Lesson,
    Recommendation,
    Regulation,
    Relationship,
    WorkOrder,
)

_ID_NAMESPACE = uuid.UUID("7c9c9b7e-2f0a-4a4f-9d1a-0b6e0f7a0a11")


def det_id(*parts: str) -> str:
    """Deterministic id derived from a natural key, so document/entity IDs
    stay stable across repeated `POST /ingestion/seed` calls — required so
    `data/eval/questions.json` can hardcode expected_document_ids /
    expected_entity_ids that remain valid after every reseed."""
    return uuid.uuid5(_ID_NAMESPACE, "|".join(parts)).hex


SAMPLE_CORPUS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "sample_corpus",
)


def _wipe(db: Session) -> None:
    for model in [
        Relationship,
        Entity,
        Chunk,
        Document,
        ComplianceGap,
        Lesson,
        Recommendation,
        Inspection,
        Incident,
        WorkOrder,
        Regulation,
        Asset,
        BenchmarkQuestion,
        IngestionRun,
    ]:
        db.execute(delete(model))
    db.commit()


class _Registry:
    """Dedups entities globally by (entity_type, ref_code-or-label)."""

    def __init__(self, db: Session):
        self.db = db
        self._by_key: dict[tuple[str, str], Entity] = {}

    def get_or_create(self, entity_type: str, label: str, ref_code: str | None,
                       source_document_id: str | None) -> Entity:
        key = (entity_type, ref_code or label)
        existing = self._by_key.get(key)
        if existing is not None:
            # Record "first-seen document" the first time we learn it, even
            # if this entity was pre-registered (e.g. canonical assets)
            # before any document had been ingested yet.
            if existing.source_document_id is None and source_document_id is not None:
                existing.source_document_id = source_document_id
            return existing
        ent = Entity(
            id=det_id("entity", entity_type, ref_code or label),
            entity_type=entity_type,
            label=label,
            ref_code=ref_code,
            source_document_id=source_document_id,
        )
        self.db.add(ent)
        self.db.flush()
        self._by_key[key] = ent
        return ent

    def find(self, entity_type: str, ref_code: str) -> Entity | None:
        return self._by_key.get((entity_type, ref_code))


def _link(db: Session, source: Entity, target: Entity, rel_type: str, weight: float = 1.0,
          _dedup: set | None = None) -> None:
    if source.id == target.id:
        return
    if _dedup is not None:
        key = (source.id, target.id, rel_type)
        if key in _dedup:
            return
        _dedup.add(key)
    db.add(Relationship(
        source_entity_id=source.id,
        target_entity_id=target.id,
        relationship_type=rel_type,
        weight=weight,
    ))


def run_seed(db: Session) -> dict:
    """Wipe + reseed everything. Returns the ingestion-summary dict used by
    both POST /ingestion/seed and GET /ingestion/status."""

    generate_corpus(SAMPLE_CORPUS_DIR)
    _wipe(db)

    # ---- 1. structured operational tables -------------------------------
    assets_by_tag: dict[str, Asset] = {}
    for a in ASSETS:
        row = Asset(id=det_id("asset", a["tag"]), tag=a["tag"], name=a["name"],
                     asset_type=a["asset_type"], criticality=a["criticality"],
                     location=a["location"], risk_score=0.0)
        db.add(row)
        assets_by_tag[a["tag"]] = row
    db.flush()

    regs_by_code: dict[str, Regulation] = {}
    for r in REGULATIONS:
        row = Regulation(id=det_id("regulation", r["code"]), code=r["code"],
                          title=r["title"], description=r["description"])
        db.add(row)
        regs_by_code[r["code"]] = row
    db.flush()

    work_orders_by_number: dict[str, WorkOrder] = {}
    for wo in WORK_ORDERS:
        asset = assets_by_tag.get(wo["asset_tag"])
        row = WorkOrder(
            id=det_id("work_order", wo["wo_number"]),
            wo_number=wo["wo_number"],
            asset_id=asset.id if asset else None,
            description=wo["description"],
            failure_mode=wo["failure_mode"],
            status=wo["status"],
            opened_at=datetime.fromisoformat(wo["opened_at"]),
            closed_at=datetime.fromisoformat(wo["closed_at"]) if wo["closed_at"] else None,
        )
        db.add(row)
        work_orders_by_number[wo["wo_number"]] = row
    db.flush()

    incidents_by_code: dict[str, Incident] = {}
    for inc in INCIDENTS:
        asset = assets_by_tag.get(inc["asset_tag"])
        row = Incident(
            id=det_id("incident", inc["incident_code"]),
            incident_code=inc["incident_code"],
            asset_id=asset.id if asset else None,
            title=inc["title"],
            summary=inc["summary"],
            severity=inc["severity"],
            occurred_at=datetime.fromisoformat(inc["occurred_at"]),
        )
        db.add(row)
        incidents_by_code[inc["incident_code"]] = row
    db.flush()

    inspections_by_filename: dict[str, Inspection] = {}
    for insp in INSPECTIONS:
        asset = assets_by_tag.get(insp["asset_tag"])
        row = Inspection(
            asset_id=asset.id if asset else None,
            inspector=insp["inspector"],
            checklist_item=insp["checklist_item"],
            result=insp["result"],
            inspected_at=datetime.fromisoformat(insp["inspected_at"]),
        )
        db.add(row)
        inspections_by_filename[insp["filename"]] = row
    db.flush()

    gap_asset = assets_by_tag.get(COMPLIANCE_GAP["asset_tag"])
    gap_reg = regs_by_code.get(COMPLIANCE_GAP["regulation_code"])
    compliance_gap_row = ComplianceGap(
        asset_id=gap_asset.id if gap_asset else None,
        checklist_item=COMPLIANCE_GAP["checklist_item"],
        regulation_id=gap_reg.id if gap_reg else None,
        status=COMPLIANCE_GAP["status"],
        severity=COMPLIANCE_GAP["severity"],
        missing_evidence=COMPLIANCE_GAP["missing_evidence"],
        corrective_action=COMPLIANCE_GAP["corrective_action"],
    )
    db.add(compliance_gap_row)
    db.flush()

    # A couple of standing recommendations tied to the P-101 story and the
    # B-12 compliance gap, surfaced via Asset 360 / Copilot.
    db.add(Recommendation(
        asset_id=assets_by_tag["P-101"].id,
        action="Monitor P-101 vibration weekly and confirm cartridge seal (WO-1089) performance at each round.",
        rationale="Three prior mechanical seal failures (WO-1041, WO-1052, WO-1067) and incident IR-07 indicate a recurring failure pattern driven by cavitation/misalignment.",
        priority="high",
    ))
    db.add(Recommendation(
        asset_id=assets_by_tag["B-12"].id,
        action="Schedule certified bench test for Relief Valve V-045 and file the certificate.",
        rationale="No 2025 test certificate on file; REG-052 / REG-014 require current evidence, tracked under WO-1102.",
        priority="high",
    ))
    db.flush()

    # ---- 2. document ingestion: parse -> chunk -> extract -> embed -------
    manifest_path = os.path.join(SAMPLE_CORPUS_DIR, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    registry = _Registry(db)
    provider = get_embedding_provider()
    rel_dedup: set = set()

    # Pre-register canonical entities so document-level regex matches link
    # to the *same* entity rows as the structured tables above.
    for tag, asset_row in assets_by_tag.items():
        registry.get_or_create("asset", asset_row.name, tag, None)
    for code, reg_row in regs_by_code.items():
        registry.get_or_create("regulation", reg_row.title, code, None)
    for wo_number, wo_row in work_orders_by_number.items():
        registry.get_or_create("work_order", wo_number, wo_number, None)
    for code, inc_row in incidents_by_code.items():
        registry.get_or_create("incident", inc_row.title, code, None)

    documents_ingested = 0
    chunks_created = 0
    doc_entity_by_id: dict[str, Entity] = {}

    for entry in manifest:
        filename = entry["filename"]
        doc_type = entry["doc_type"]
        title = entry["title"]
        path = os.path.join(SAMPLE_CORPUS_DIR, filename)

        parsed = ingestion.parse_file(path)
        text = parsed.text
        source_path = os.path.relpath(path, os.path.dirname(SAMPLE_CORPUS_DIR)).replace("\\", "/")

        doc = Document(
            id=det_id("document", source_path),
            title=title,
            doc_type=doc_type,
            source_path=source_path,
            raw_text=text,
        )
        db.add(doc)
        db.flush()
        documents_ingested += 1

        # document-level pseudo-entity so it can participate in relationships
        doc_entity_type = "procedure" if doc_type == "sop" else ("inspection" if doc_type == "inspection" else "document")
        doc_entity = registry.get_or_create(doc_entity_type, title, None, doc.id)
        doc_entity_by_id[doc.id] = doc_entity

        # chunk + embed
        for idx, chunk_text_val, start, end in ingestion.chunk_text(text):
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=idx,
                text=chunk_text_val,
                char_start=start,
                char_end=end,
                embedding="[]",
            )
            db.add(chunk)
            db.flush()
            embedding = provider.embed(chunk_text_val)
            vector_backend.upsert(db, chunk.id, embedding)
            chunks_created += 1

        # entity extraction over the full document text
        extracted = ingestion.extract_entities(text, PEOPLE)
        mentioned_assets: list[Entity] = []
        mentioned_regs: list[Entity] = []
        for ex in extracted:
            ent = registry.get_or_create(ex.entity_type, ex.label, ex.ref_code, doc.id)
            if ex.entity_type == "asset":
                mentioned_assets.append(ent)
                edge_type = "asset->procedure" if doc_type == "sop" else "asset->document"
                _link(db, ent, doc_entity, edge_type, _dedup=rel_dedup)
            elif ex.entity_type == "regulation":
                mentioned_regs.append(ent)

        # incident->regulation edges, when this doc is an incident write-up
        if doc_type == "incident":
            incident_code = next((e.ref_code for e in extracted if e.entity_type == "incident"), None)
            if incident_code:
                inc_entity = registry.find("incident", incident_code)
                if inc_entity:
                    for reg_ent in mentioned_regs:
                        _link(db, inc_entity, reg_ent, "incident->regulation", _dedup=rel_dedup)

        # inspection->compliance_gap edge for the B-12 Q4 inspection doc
        if filename == "inspection_b12_relief_valve_2025q4.txt":
            gap_entity = registry.get_or_create(
                "compliance_gap", compliance_gap_row.checklist_item, None, doc.id
            )
            _link(db, doc_entity, gap_entity, "inspection->compliance_gap", _dedup=rel_dedup)

    # ---- 3. structured relationship edges (asset->work_order/incident,
    #         work_order->failure_mode) driven directly from the
    #         operational tables for reliability -----------------------
    for wo in WORK_ORDERS:
        asset_ent = registry.find("asset", wo["asset_tag"])
        wo_ent = registry.find("work_order", wo["wo_number"])
        if asset_ent and wo_ent:
            _link(db, asset_ent, wo_ent, "asset->work_order", _dedup=rel_dedup)
        if wo["failure_mode"] and wo_ent:
            fm_ent = registry.get_or_create(
                "failure_mode", wo["failure_mode"], None, wo_ent.source_document_id
            )
            _link(db, wo_ent, fm_ent, "work_order->failure_mode", _dedup=rel_dedup)

    for inc in INCIDENTS:
        asset_ent = registry.find("asset", inc["asset_tag"])
        inc_ent = registry.find("incident", inc["incident_code"])
        if asset_ent and inc_ent:
            _link(db, asset_ent, inc_ent, "asset->incident", _dedup=rel_dedup)
        for reg_code in inc.get("regulation_codes", []):
            reg_ent = registry.find("regulation", reg_code)
            if reg_ent and inc_ent:
                _link(db, inc_ent, reg_ent, "incident->regulation", _dedup=rel_dedup)

    # ---- 4. incident->incident similarity edges (lessons-learned) --------
    incident_codes = list(incidents_by_code.keys())
    incident_texts = {code: incidents_by_code[code].summary for code in incident_codes}
    embeddings_by_code = {code: provider.embed(text) for code, text in incident_texts.items()}

    import numpy as np

    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    SIMILARITY_THRESHOLD = 0.12
    for i, code_a in enumerate(incident_codes):
        best_code, best_score = None, -1.0
        for code_b in incident_codes:
            if code_a == code_b:
                continue
            score = cosine(embeddings_by_code[code_a], embeddings_by_code[code_b])
            if score > best_score:
                best_code, best_score = code_b, score
        if best_code and best_score >= SIMILARITY_THRESHOLD:
            inc_a = incidents_by_code[code_a]
            inc_b = incidents_by_code[best_code]
            db.add(Lesson(
                incident_id=inc_a.id,
                similar_incident_id=inc_b.id,
                similarity=round(best_score, 3),
                warning_text=f"This resembles Incident {inc_b.incident_code} ({inc_b.title}).",
            ))
            ent_a = registry.find("incident", code_a)
            ent_b = registry.find("incident", best_code)
            if ent_a and ent_b:
                _link(db, ent_a, ent_b, "incident->incident", weight=round(best_score, 3), _dedup=rel_dedup)

    # ---- 5. benchmark questions -------------------------------------------
    _load_benchmark_questions(db)

    # Relationship rows added via _link() above are not individually flushed
    # (autoflush is off for this session), so force a flush before counting
    # or these counts would silently undercount what's actually in the DB.
    db.flush()
    entities_extracted = db.query(Entity).count()
    relationships_created = db.query(Relationship).count()

    run = IngestionRun(
        documents_ingested=documents_ingested,
        chunks_created=chunks_created,
        entities_extracted=entities_extracted,
        relationships_created=relationships_created,
    )
    db.add(run)
    db.commit()

    # ---- 6. derive asset risk scores now that everything is committed ----
    _update_risk_scores(db)
    db.commit()

    return {
        "documents_ingested": documents_ingested,
        "chunks_created": chunks_created,
        "entities_extracted": entities_extracted,
        "relationships_created": relationships_created,
    }


def _update_risk_scores(db: Session) -> None:
    for asset in db.query(Asset).all():
        wo_count = db.query(WorkOrder).filter(WorkOrder.asset_id == asset.id).count()
        inc_count = db.query(Incident).filter(Incident.asset_id == asset.id).count()
        gap_count = db.query(ComplianceGap).filter(
            ComplianceGap.asset_id == asset.id, ComplianceGap.status != "ok"
        ).count()
        criticality_weight = {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}.get(
            asset.criticality, 1.0
        )
        score = (wo_count * 0.15 + inc_count * 0.3 + gap_count * 0.4) * criticality_weight
        asset.risk_score = round(min(score, 10.0), 2)


def _load_benchmark_questions(db: Session) -> None:
    eval_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
        "eval",
        "questions.json",
    )
    if not os.path.exists(eval_path):
        return
    with open(eval_path, "r", encoding="utf-8") as fh:
        questions = json.load(fh)
    for q in questions:
        db.add(BenchmarkQuestion(
            id=q.get("id"),
            question=q["question"],
            expected_document_ids=json.dumps(q.get("expected_document_ids", [])),
            expected_entity_ids=json.dumps(q.get("expected_entity_ids", [])),
            expects_citation=q.get("expects_citation", True),
        ))
