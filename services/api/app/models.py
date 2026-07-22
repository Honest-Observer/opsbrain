"""SQLAlchemy models mirroring packages/shared/schema.md.

Every table listed in schema.md is implemented here 1:1. IDs are string UUIDs
(hex, no dashes) so they work identically on SQLite and Postgres without
requiring a native UUID column type. The `chunks.embedding` column stores a
JSON-encoded list[float] as TEXT so it works unmodified on both backends; the
vector-search *behavior* (pgvector vs. numpy cosine) lives behind the
interface in `db.py`, not in the column type itself (see ADR-004).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    tag: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    asset_type: Mapped[str] = mapped_column(String(64))
    criticality: Mapped[str] = mapped_column(String(16), default="medium")
    location: Mapped[str] = mapped_column(String(255), default="")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    source_path: Mapped[str] = mapped_column(String(500), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(32), ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)
    # JSON-encoded list[float]. See db.py VectorBackend for how this is
    # searched (numpy cosine on SQLite, pgvector <=> operator on Postgres
    # when the extension is available).
    embedding: Mapped[str] = mapped_column(Text, default="[]")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(255))
    ref_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_document_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("documents.id"), nullable=True
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    source_entity_id: Mapped[str] = mapped_column(String(32), ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[str] = mapped_column(String(32), ForeignKey("entities.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    wo_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    asset_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("assets.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    failure_mode: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    incident_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    asset_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("assets.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    asset_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("assets.id"), nullable=True)
    inspector: Mapped[str] = mapped_column(String(255), default="")
    checklist_item: Mapped[str] = mapped_column(String(255), default="")
    result: Mapped[str] = mapped_column(String(16), default="not_recorded")
    inspected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Regulation(Base):
    __tablename__ = "regulations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")


class ComplianceGap(Base):
    __tablename__ = "compliance_gaps"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    asset_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("assets.id"), nullable=True)
    checklist_item: Mapped[str] = mapped_column(String(255), default="")
    regulation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("regulations.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default="gap")
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    missing_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.id"))
    similar_incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.id"))
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    warning_text: Mapped[str] = mapped_column(String(500), default="")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    asset_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("assets.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(500))
    rationale: Mapped[str] = mapped_column(String(500), default="")
    priority: Mapped[str] = mapped_column(String(16), default="medium")


class BenchmarkQuestion(Base):
    __tablename__ = "benchmark_questions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    question: Mapped[str] = mapped_column(Text)
    # Stored as JSON-encoded string lists (portable across SQLite/Postgres
    # without requiring native ARRAY support).
    expected_document_ids: Mapped[str] = mapped_column(Text, default="[]")
    expected_entity_ids: Mapped[str] = mapped_column(Text, default="[]")
    expects_citation: Mapped[bool] = mapped_column(Boolean, default=True)


class IngestionRun(Base):
    """Bookkeeping row so GET /ingestion/status can report last_seeded_at."""

    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    seeded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    documents_ingested: Mapped[int] = mapped_column(Integer, default=0)
    chunks_created: Mapped[int] = mapped_column(Integer, default=0)
    entities_extracted: Mapped[int] = mapped_column(Integer, default=0)
    relationships_created: Mapped[int] = mapped_column(Integer, default=0)
