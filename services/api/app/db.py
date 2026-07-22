"""Database layer (ADR-004).

Tries Postgres via the `DATABASE_URL` env var first; if it's not set, or the
connection isn't reachable, falls back automatically to a local SQLite file
at `services/api/opsbrain.db`. Callers (routers/services) only ever import
`get_engine`, `SessionLocal`, `init_db`, `get_db`, and `vector_backend` from
this module — they never branch on which backend is actually active.

Vector similarity is wrapped behind `VectorBackend` so the rest of the app
doesn't care whether it's pgvector or an in-process numpy cosine search:
- Postgres + pgvector extension available -> `PgVectorBackend` (SQL `<=>`).
- Anything else (SQLite, or Postgres without the extension) ->
  `NumpyCosineBackend`, which loads the JSON-encoded embedding column into
  memory and ranks with cosine similarity.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Iterator

import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "opsbrain.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"


def _try_postgres(url: str):
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None


def _build_engine():
    database_url = os.environ.get("DATABASE_URL", "").strip()
    backend_name = "sqlite"
    engine = None
    if database_url and not database_url.startswith("sqlite"):
        engine = _try_postgres(database_url)
        if engine is not None:
            backend_name = "postgres"
    if engine is None:
        sqlite_url = database_url if database_url.startswith("sqlite") else DEFAULT_SQLITE_URL
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        backend_name = "sqlite"
    return engine, backend_name


engine, BACKEND_NAME = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

PGVECTOR_AVAILABLE = False
if BACKEND_NAME == "postgres":
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        PGVECTOR_AVAILABLE = True
    except Exception:
        PGVECTOR_AVAILABLE = False


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if PGVECTOR_AVAILABLE:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_vec vector(256)"
                    )
                )
        except Exception:
            pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class VectorBackend:
    """Common interface: upsert an embedding for a chunk, search top_k."""

    def upsert(self, db: Session, chunk_id: str, embedding: list[float]) -> None:
        raise NotImplementedError

    def search(self, db: Session, query_embedding: list[float], top_k: int = 5) -> list[tuple[str, float]]:
        raise NotImplementedError


class NumpyCosineBackend(VectorBackend):
    """Default backend: works identically on SQLite and plain Postgres."""

    def upsert(self, db: Session, chunk_id: str, embedding: list[float]) -> None:
        from .models import Chunk

        chunk = db.get(Chunk, chunk_id)
        if chunk is not None:
            chunk.embedding = json.dumps(embedding)

    def search(self, db: Session, query_embedding: list[float], top_k: int = 5) -> list[tuple[str, float]]:
        from .models import Chunk

        q = np.array(query_embedding, dtype=float)
        scored: list[tuple[str, float]] = []
        for chunk_id, raw in db.query(Chunk.id, Chunk.embedding).all():
            if not raw or raw == "[]":
                continue
            try:
                vec = np.array(json.loads(raw), dtype=float)
            except Exception:
                continue
            if vec.shape != q.shape:
                continue
            scored.append((chunk_id, _cosine(q, vec)))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:top_k]


class PgVectorBackend(VectorBackend):
    """Used only when Postgres + the pgvector extension are both available."""

    def upsert(self, db: Session, chunk_id: str, embedding: list[float]) -> None:
        from .models import Chunk

        chunk = db.get(Chunk, chunk_id)
        if chunk is not None:
            chunk.embedding = json.dumps(embedding)
        try:
            db.execute(
                text("UPDATE chunks SET embedding_vec = :vec WHERE id = :id"),
                {"vec": str(embedding), "id": chunk_id},
            )
        except Exception:
            pass

    def search(self, db: Session, query_embedding: list[float], top_k: int = 5) -> list[tuple[str, float]]:
        try:
            rows = db.execute(
                text(
                    "SELECT id, 1 - (embedding_vec <=> :vec) AS score FROM chunks "
                    "WHERE embedding_vec IS NOT NULL ORDER BY embedding_vec <=> :vec LIMIT :k"
                ),
                {"vec": str(query_embedding), "k": top_k},
            ).all()
            return [(row[0], float(row[1])) for row in rows]
        except Exception:
            return NumpyCosineBackend().search(db, query_embedding, top_k)


vector_backend: VectorBackend = PgVectorBackend() if PGVECTOR_AVAILABLE else NumpyCosineBackend()
