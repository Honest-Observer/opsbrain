"""Unit tests for the ingestion pipeline: parsing, chunking, entity extraction."""
from __future__ import annotations

import os

from app.corpus_generator import PEOPLE
from app.ingestion import chunk_text, extract_entities, parse_file

CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                          "data", "sample_corpus")


def test_chunk_text_reconstructs_offsets():
    text = "word " * 500
    chunks = chunk_text(text, target_words=300)
    assert len(chunks) >= 1
    for idx, chunk_str, start, end in chunks:
        assert text[start:end] == chunk_str


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []


def test_extract_entities_finds_known_codes():
    text = "Pump P-101 failed again; see WO-1067 and Incident IR-07, per REG-022, dated 2025-08-20. Raj Patel investigated."
    found = extract_entities(text, PEOPLE)
    by_type = {}
    for e in found:
        by_type.setdefault(e.entity_type, []).append(e.ref_code or e.label)
    assert "P-101" in by_type["asset"]
    assert "WO-1067" in by_type["work_order"]
    assert "IR-07" in by_type["incident"]
    assert "REG-022" in by_type["regulation"]
    assert "2025-08-20" in by_type["date"]
    assert "Raj Patel" in by_type["person"]


def test_extract_entities_excludes_non_asset_prefixes():
    text = "WO-1067 and IR-07 and REG-022 should not be misidentified as assets."
    found = [e for e in extract_entities(text, PEOPLE) if e.entity_type == "asset"]
    assert found == []


def test_parse_pdf():
    parsed = parse_file(os.path.join(CORPUS_DIR, "manual_pump_p101_oem.pdf"))
    assert "P-101" in parsed.text
    assert parsed.metadata["doc_type"] == "manual"


def test_parse_json_work_order():
    parsed = parse_file(os.path.join(CORPUS_DIR, "wo_1041.json"))
    assert "WO-1041" in parsed.text
    assert parsed.metadata["structured"]["wo_number"] == "WO-1041"


def test_parse_csv_asset_registry():
    parsed = parse_file(os.path.join(CORPUS_DIR, "asset_registry.csv"))
    assert "P-101" in parsed.text
    assert isinstance(parsed.metadata["structured"], list)
    assert len(parsed.metadata["structured"]) >= 6


def test_parse_xlsx_compliance_audit():
    parsed = parse_file(os.path.join(CORPUS_DIR, "compliance_audit_checklist.xlsx"))
    assert "B-12" in parsed.text


def test_parse_scan_txt_as_inspection():
    parsed = parse_file(os.path.join(CORPUS_DIR, "inspection_c201_2025q4.scan.txt"))
    assert parsed.metadata["doc_type"] == "inspection"
    assert "C-201" in parsed.text


def test_parse_markdown_sop():
    parsed = parse_file(os.path.join(CORPUS_DIR, "sop_pump_seal_replacement.md"))
    assert parsed.metadata["doc_type"] == "sop"
    assert "seal" in parsed.text.lower()
