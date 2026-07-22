"""Pluggable local embedding provider (ADR-008).

Default implementation is a deterministic hash-based bag-of-words embedding:
no model download, no network call, no API key, and it is 100% reproducible
run-to-run (important for the eval harness). It is deliberately simple — a
signed feature-hashing scheme over lowercased word tokens, L2-normalized —
which is enough to make cosine similarity meaningfully cluster related
industrial-maintenance text (shared vocabulary like "seal", "pump",
"pressure", "relief valve" dominate the signal) without any ML dependency.

Swap in a real embedding API later by implementing `EmbeddingProvider` and
changing `get_embedding_provider()` — no caller elsewhere needs to change.
"""
from __future__ import annotations

import hashlib
import re
from typing import Protocol

EMBEDDING_DIM = 256
# Preserve hyphenated codes (p-101, wo-1041, ir-07, reg-052) as single
# tokens instead of splitting on the hyphen — these are the highest-signal
# words in this domain and must not be diluted into bare numbers.
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# A small stopword list. Filtering these out matters a lot for a bag-of-hash
# embedding with no corpus-wide IDF weighting: without it, common function
# words dominate cosine similarity and drown out the domain vocabulary
# (asset tags, failure modes, regulation codes) that should drive retrieval
# and incident-similarity matching.
_STOPWORDS = frozenset("""
a an the and or but if while of to in on at by for with from into onto
is are was were be been being do does did done has have had having
this that these those it its it's as than then so such not no nor
will would shall should can could may might must
i you he she we they them his her our your their
about above after again against all am any because before below between
both down during each few further here how just more most once only other
over own same some there through under until up very when where which who
whom why yourselves ourselves themselves
""".split())

_CODE_LIKE_RE = re.compile(r"^[a-z]{1,3}-\d+$|^\d{3,4}$")


class EmbeddingProvider(Protocol):
    dim: int

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class LocalHashEmbeddingProvider:
    """Deterministic, dependency-free embedding via signed feature hashing."""

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def _tokenize(self, text: str) -> list[str]:
        tokens = _TOKEN_RE.findall(text.lower())
        return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = self._tokenize(text)
        if not tokens:
            return vec
        for tok in tokens:
            digest = hashlib.sha256(tok.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            # Domain codes (p-101, wo-1041, ir-07, reg-052, bare 3-4 digit
            # numbers) are the highest-signal tokens in this corpus, so they
            # get extra weight relative to ordinary words.
            weight = 2.5 if _CODE_LIKE_RE.match(tok) else 1.0
            vec[idx] += sign * weight
        # L2 normalize so cosine similarity behaves well.
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class GeminiEmbeddingProvider:
    """Real semantic embeddings via the Gemini embedding API (ADR-008 swap).

    Only selected when a GEMINI_API_KEY is configured. Vectors are
    L2-normalized by the client, so cosine similarity behaves cleanly against
    the same NumpyCosineBackend used for the local provider — no other code in
    the app needs to change when this is active.
    """

    def __init__(self, dim: int):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        from .gemini_client import embed as gemini_embed

        return gemini_embed(text, dim=self.dim)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


_local_provider: EmbeddingProvider | None = None
_gemini_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Return the active embedding provider.

    Chosen fresh each call based on config so the app can boot before a key is
    known and pick it up on the next request. Instances are cached per mode.
    """
    from .config import gemini_embed_dim, gemini_enabled

    global _local_provider, _gemini_provider
    if gemini_enabled():
        if _gemini_provider is None:
            _gemini_provider = GeminiEmbeddingProvider(gemini_embed_dim())
        return _gemini_provider
    if _local_provider is None:
        _local_provider = LocalHashEmbeddingProvider()
    return _local_provider
