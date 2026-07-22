"""LLM-based entity + relationship extraction for arbitrary uploaded documents.

The seeded demo corpus uses deterministic structured extraction (see seed.py)
to keep the crafted demo crisp. But when a user uploads *arbitrary* raw data,
regex alone can't understand it — so when Gemini is configured we ask the model
to read the document and return a normalized set of entities and relationships
that plug straight into the same knowledge-graph tables.

Falls back to `None` (caller then uses the regex path) if Gemini is off or the
call fails, so uploads never hard-fail.
"""
from __future__ import annotations

# Canonical entity/relationship vocabulary — kept aligned with the seeded graph
# so LLM-extracted nodes/edges are consistent with the rest of the system.
ENTITY_TYPES = [
    "asset", "work_order", "incident", "regulation", "procedure",
    "failure_mode", "component", "person", "date",
]
RELATIONSHIP_TYPES = [
    "asset->document", "asset->work_order", "asset->incident",
    "incident->regulation", "asset->procedure", "work_order->failure_mode",
    "asset->component", "incident->incident",
]


def extract_graph(text: str, max_chars: int = 12000) -> dict | None:
    """Return {"entities": [...], "relationships": [...]} or None on failure."""
    from .config import gemini_enabled

    if not gemini_enabled():
        return None

    from .gemini_client import generate_json

    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "entity_type": {"type": "string", "enum": ENTITY_TYPES},
                        "label": {"type": "string"},
                        "ref_code": {"type": "string"},
                    },
                    "required": ["entity_type", "label"],
                },
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_label": {"type": "string"},
                        "target_label": {"type": "string"},
                        "relationship_type": {"type": "string", "enum": RELATIONSHIP_TYPES},
                    },
                    "required": ["source_label", "target_label", "relationship_type"],
                },
            },
        },
        "required": ["entities", "relationships"],
    }

    prompt = (
        "You are an industrial knowledge-graph extractor. Read the DOCUMENT below and extract "
        "the entities and the relationships between them, for a plant asset & operations "
        "knowledge graph.\n\n"
        f"Allowed entity_type values: {', '.join(ENTITY_TYPES)}.\n"
        f"Allowed relationship_type values: {', '.join(RELATIONSHIP_TYPES)}.\n"
        "Rules:\n"
        "- Use ref_code for identifiers like asset tags (e.g. P-101), work orders (WO-1234), "
        "incidents (IR-07), regulations (REG-014); omit ref_code for people/dates/free-text.\n"
        "- source_label/target_label in relationships MUST exactly match a label you listed in "
        "entities.\n"
        "- Only extract what is actually supported by the document. Do not invent codes.\n\n"
        f"DOCUMENT:\n{text[:max_chars]}"
    )

    try:
        result = generate_json(prompt, schema, max_output_tokens=8192)
    except Exception:
        return None

    if not isinstance(result, dict):
        return None
    entities = result.get("entities") or []
    relationships = result.get("relationships") or []
    # Light validation/normalization.
    clean_entities = []
    for e in entities:
        if not isinstance(e, dict) or e.get("entity_type") not in ENTITY_TYPES:
            continue
        label = str(e.get("label", "")).strip()
        if not label:
            continue
        ref = e.get("ref_code")
        clean_entities.append({
            "entity_type": e["entity_type"],
            "label": label,
            "ref_code": str(ref).strip() if ref else None,
        })
    clean_rels = []
    for r in relationships:
        if not isinstance(r, dict) or r.get("relationship_type") not in RELATIONSHIP_TYPES:
            continue
        s = str(r.get("source_label", "")).strip()
        t = str(r.get("target_label", "")).strip()
        if not s or not t:
            continue
        clean_rels.append({
            "source_label": s, "target_label": t,
            "relationship_type": r["relationship_type"],
        })
    return {"entities": clean_entities, "relationships": clean_rels}
