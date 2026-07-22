"""Runtime configuration + optional Gemini (Google AI Studio) integration flags.

The whole app degrades gracefully: with NO `GEMINI_API_KEY` set, every Gemini
code path is skipped and OpsBrain runs fully offline on deterministic local
embeddings + template answers (the original behaviour). With a key present,
embeddings, copilot answer generation, and arbitrary-document graph extraction
all upgrade to real Gemini calls.

Key resolution order:
1. If `OPSBRAIN_DISABLE_GEMINI` is truthy -> Gemini is forced OFF (used by the
   test suite so tests stay offline/deterministic regardless of any `.env`).
2. Otherwise the key is read from the `GEMINI_API_KEY` env var, which may be
   supplied directly or via a git-ignored `services/api/.env` file.

Supports whatever key format Google AI Studio issues (both the classic
`AIza...` keys and the newer `AQ.*` keys) — the key is sent verbatim as the
`x-goog-api-key` header, so the format is irrelevant to this code.
"""
from __future__ import annotations

import os

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def _load_dotenv() -> None:
    """Load services/api/.env WITHOUT overriding already-set process env vars."""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(_ENV_PATH, override=False)
        return
    except Exception:
        pass
    # Minimal fallback parser so we don't hard-depend on python-dotenv.
    if not os.path.exists(_ENV_PATH):
        return
    try:
        with open(_ENV_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except Exception:
        pass


_load_dotenv()


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


def gemini_api_key() -> str:
    if _truthy(os.environ.get("OPSBRAIN_DISABLE_GEMINI")):
        return ""
    return os.environ.get("GEMINI_API_KEY", "").strip()


def gemini_enabled() -> bool:
    return bool(gemini_api_key())


def gemini_chat_model() -> str:
    return os.environ.get("GEMINI_CHAT_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"


def gemini_embed_model() -> str:
    return os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001").strip() or "gemini-embedding-001"


def gemini_embed_dim() -> int:
    try:
        return int(os.environ.get("GEMINI_EMBED_DIM", "768"))
    except ValueError:
        return 768


def ai_mode() -> str:
    """Human-facing label for the active reasoning backend."""
    return "gemini" if gemini_enabled() else "local"


def ai_model_label() -> str:
    return gemini_chat_model() if gemini_enabled() else "local-heuristic"
