"""Thin REST client for the Google Gemini API (Google AI Studio).

Uses the `v1beta` generativelanguage endpoint with `x-goog-api-key` auth, which
works for both classic `AIza...` keys and the newer `AQ.*` AI Studio keys.

Only two capabilities are needed by OpsBrain:
- `embed(text)`               -> a single embedding vector (L2-normalized)
- `generate_json(prompt, schema)` -> structured JSON output (for the copilot
                                 and for arbitrary-document graph extraction)

Everything raises `GeminiError` on failure so callers can cleanly fall back to
the offline/deterministic path instead of 500-ing the request.
"""
from __future__ import annotations

import json
import math
import time

import httpx

from .config import (
    gemini_api_key,
    gemini_chat_model,
    gemini_embed_dim,
    gemini_embed_model,
)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiError(Exception):
    pass


def _headers() -> dict:
    key = gemini_api_key()
    if not key:
        raise GeminiError("No GEMINI_API_KEY configured")
    return {"x-goog-api-key": key, "Content-Type": "application/json"}


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _post_with_retry(url: str, body: dict, timeout: float, retries: int = 3) -> httpx.Response:
    """POST with exponential backoff on rate limits / transient server errors.

    The free Gemini tier enforces a low requests-per-minute cap, so 429s are
    expected under bursty load (seeding + upload + copilot). Retry those (and
    502/503/504) with backoff instead of failing the whole operation.
    """
    backoff = 2.0
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = httpx.post(url, headers=_headers(), json=body, timeout=timeout)
            if resp.status_code in (429, 502, 503, 504) and attempt < retries:
                # Honour Retry-After if present, else exponential backoff.
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                time.sleep(min(delay, 30.0))
                backoff *= 2
                continue
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError:
            raise
        except Exception as e:  # noqa: BLE001 - transient network errors get retried
            last_exc = e
            if attempt < retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    if last_exc:
        raise last_exc
    raise GeminiError("request failed")


def _extract_text(response_json: dict) -> str:
    """Concatenate all text parts of the first candidate (Gemini 3.x thinking
    models may emit multiple parts; we keep the visible text ones)."""
    candidates = response_json.get("candidates") or []
    if not candidates:
        raise GeminiError(f"No candidates in Gemini response: {response_json}")
    parts = candidates[0].get("content", {}).get("parts", []) or []
    texts = [p["text"] for p in parts if isinstance(p, dict) and "text" in p]
    if not texts:
        raise GeminiError("No text parts in Gemini response")
    return "".join(texts).strip()


def embed(text: str, dim: int | None = None, timeout: float = 30.0, retries: int = 1) -> list[float]:
    model = gemini_embed_model()
    dim = dim if dim is not None else gemini_embed_dim()
    body: dict = {
        "model": f"models/{model}",
        "content": {"parts": [{"text": (text or " ")[:8000]}]},
    }
    if dim:
        body["outputDimensionality"] = dim

    url = f"{BASE_URL}/models/{model}:embedContent"
    try:
        resp = _post_with_retry(url, body, timeout=timeout, retries=retries + 2)
        values = resp.json().get("embedding", {}).get("values")
        if not values:
            raise GeminiError("Empty embedding returned")
        return _l2_normalize([float(v) for v in values])
    except GeminiError:
        raise
    except Exception as e:  # noqa: BLE001
        raise GeminiError(f"Gemini embed failed: {e}")


def _loads_lenient(raw: str) -> dict:
    """Parse JSON, tolerating markdown fences or trailing prose around it."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.lstrip().lower().startswith("json"):
            raw = raw.lstrip()[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Salvage the outermost {...} object if there's extra text around it.
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start:end + 1])
        raise


def generate_json(prompt: str, schema: dict, timeout: float = 90.0,
                  max_output_tokens: int = 8192, temperature: float = 0.2,
                  thinking_level: str = "low") -> dict:
    model = gemini_chat_model()
    generation_config: dict = {
        "responseMimeType": "application/json",
        "responseSchema": schema,
        "maxOutputTokens": max_output_tokens,
        "temperature": temperature,
    }
    # Bound "thinking" so it can't eat the whole output-token budget and
    # truncate the JSON (Gemini 3.x flash is a thinking model).
    if thinking_level:
        generation_config["thinkingConfig"] = {"thinkingLevel": thinking_level}

    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": generation_config}
    url = f"{BASE_URL}/models/{model}:generateContent"
    try:
        resp = _post_with_retry(url, body, timeout=timeout)
        raw = _extract_text(resp.json())
        return _loads_lenient(raw)
    except GeminiError:
        raise
    except Exception as e:  # noqa: BLE001
        raise GeminiError(f"Gemini generate_json failed: {e}")


def generate_text(prompt: str, timeout: float = 60.0, max_output_tokens: int = 1024,
                  temperature: float = 0.3) -> str:
    model = gemini_chat_model()
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_output_tokens,
            "temperature": temperature,
        },
    }
    url = f"{BASE_URL}/models/{model}:generateContent"
    try:
        resp = _post_with_retry(url, body, timeout=timeout)
        return _extract_text(resp.json())
    except GeminiError:
        raise
    except Exception as e:  # noqa: BLE001
        raise GeminiError(f"Gemini generate_text failed: {e}")
