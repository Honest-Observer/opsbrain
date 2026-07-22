"""Ingestion pipeline (MASTER_SPEC §8): parse -> normalize -> chunk -> extract.

Parsers cover every format required by the spec: PDF (pypdf), TXT/MD, CSV
(pandas), XLSX (pandas/openpyxl), JSON, and a simulated scanned form
(`*.scan.txt`, parsed like plain text but tagged `doc_type` appropriately by
the caller/manifest — a deterministic stand-in for OCR per MASTER_SPEC §4
non-goals).

Entity extraction (ADR-007) is regex/heuristic and is the PRIMARY path, not
a fallback: asset tags, work order IDs, incident IDs, regulation refs,
dates, and people names (matched against a small controlled vocabulary).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import pandas as pd

# --------------------------------------------------------------------------
# Regex patterns (MASTER_SPEC §8 step 4)
# --------------------------------------------------------------------------

ASSET_TAG_RE = re.compile(r"\b([A-Z]{1,2}-\d{2,4})\b")
WORK_ORDER_RE = re.compile(r"\bWO-\d{3,6}\b")
INCIDENT_RE = re.compile(r"\bIR-\d{1,4}\b")
REGULATION_RE = re.compile(r"\b(?:REG|OSHA)-\d{2,4}\b")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

# Known non-asset codes that would otherwise false-positive on the generic
# asset-tag pattern (WO-####, IR-##, REG-###, OSHA-### all match the loose
# "[A-Z]{1,2}-digits" shape too, so asset extraction excludes them).
_NON_ASSET_PREFIXES = ("WO", "IR", "REG", "OSHA")


@dataclass
class ParsedDocument:
    text: str
    metadata: dict = field(default_factory=dict)


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _parse_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _parse_csv(path: str) -> tuple[str, list[dict]]:
    df = pd.read_csv(path)
    records = df.to_dict(orient="records")
    lines = []
    for row in records:
        lines.append(", ".join(f"{k}: {v}" for k, v in row.items()))
    return "\n".join(lines), records


def _parse_xlsx(path: str) -> tuple[str, list[dict]]:
    df = pd.read_excel(path)
    records = df.to_dict(orient="records")
    lines = []
    for row in records:
        lines.append(", ".join(f"{k}: {v}" for k, v in row.items()))
    return "\n".join(lines), records


def _parse_json(path: str) -> tuple[str, dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return json.dumps(data, indent=2), data


def parse_file(path: str) -> ParsedDocument:
    """Load + parse a single file into normalized (text, metadata).

    metadata always includes doc_type (best-effort guess; callers such as
    seed.py should override it from the corpus manifest when a canonical
    doc_type is known), source_path, title, and (for structured formats)
    a `structured` payload with the parsed rows/dict for downstream use.
    """
    filename = os.path.basename(path)
    title = os.path.splitext(filename)[0].replace("_", " ").title()
    metadata: dict = {"source_path": path, "title": title, "structured": None}

    if filename.endswith(".scan.txt"):
        text = _read_text_file(path)
        metadata["doc_type"] = "inspection"
    elif filename.endswith(".pdf"):
        text = _parse_pdf(path)
        metadata["doc_type"] = "manual"
    elif filename.endswith(".csv"):
        text, records = _parse_csv(path)
        metadata["doc_type"] = "asset_registry"
        metadata["structured"] = records
    elif filename.endswith(".xlsx"):
        text, records = _parse_xlsx(path)
        metadata["doc_type"] = "regulation"
        metadata["structured"] = records
    elif filename.endswith(".json"):
        text, data = _parse_json(path)
        metadata["doc_type"] = "work_order"
        metadata["structured"] = data
    elif filename.endswith(".md"):
        text = _read_text_file(path)
        metadata["doc_type"] = "sop"
    else:  # .txt and anything else falls back to plain text
        text = _read_text_file(path)
        metadata["doc_type"] = "handover_note"

    return ParsedDocument(text=text, metadata=metadata)


# --------------------------------------------------------------------------
# Chunking (MASTER_SPEC §8 step 3): ~250-400 "tokens" (approximated by
# whitespace-delimited words, which is a reasonable deterministic proxy
# without pulling in a real tokenizer), tracking char_start/char_end.
# --------------------------------------------------------------------------

def chunk_text(text: str, target_words: int = 300) -> list[tuple[int, str, int, int]]:
    """Return list of (chunk_index, text, char_start, char_end)."""
    words = list(re.finditer(r"\S+", text))
    if not words:
        return []
    chunks: list[tuple[int, str, int, int]] = []
    i = 0
    chunk_index = 0
    n = len(words)
    while i < n:
        j = min(i + target_words, n)
        # Avoid a tiny trailing chunk under ~50 words by folding it into the
        # previous chunk when possible.
        if n - j < 50 and j < n:
            j = n
        start_char = words[i].start()
        end_char = words[j - 1].end()
        chunks.append((chunk_index, text[start_char:end_char], start_char, end_char))
        chunk_index += 1
        i = j
    return chunks


# --------------------------------------------------------------------------
# Entity extraction (ADR-007: primary path, not a fallback)
# --------------------------------------------------------------------------

@dataclass
class ExtractedEntity:
    entity_type: str
    label: str
    ref_code: str | None


def extract_entities(text: str, people_vocab: list[str]) -> list[ExtractedEntity]:
    found: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()

    def add(entity_type: str, label: str, ref_code: str | None):
        key = (entity_type, ref_code or label)
        if key in seen:
            return
        seen.add(key)
        found.append(ExtractedEntity(entity_type, label, ref_code))

    for m in ASSET_TAG_RE.finditer(text):
        tag = m.group(1)
        prefix = tag.split("-")[0]
        if prefix in _NON_ASSET_PREFIXES:
            continue
        add("asset", tag, tag)

    for m in WORK_ORDER_RE.finditer(text):
        add("work_order", m.group(0), m.group(0))

    for m in INCIDENT_RE.finditer(text):
        add("incident", m.group(0), m.group(0))

    for m in REGULATION_RE.finditer(text):
        add("regulation", m.group(0), m.group(0))

    for m in DATE_RE.finditer(text):
        add("date", m.group(0), m.group(0))

    for person in people_vocab:
        if re.search(r"\b" + re.escape(person) + r"\b", text):
            add("person", person, None)

    return found
