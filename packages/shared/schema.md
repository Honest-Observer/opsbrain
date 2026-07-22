# Shared data model (schema.md)

Canonical entity schema. Mirrored in `services/api/app/models.py` (SQLAlchemy) and
`packages/shared/types.ts` (TypeScript). Keep all three in sync — this file is the source of
truth when they disagree.

## assets
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| tag | string | e.g. `P-101`, unique, human-referenced everywhere |
| name | string | |
| asset_type | string | pump, boiler, compressor, valve, tank, ... |
| criticality | string | low / medium / high / critical |
| location | string | |
| risk_score | float | derived: recurring issues + open compliance gaps |
| created_at | datetime | |

## documents
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| title | string | |
| doc_type | string | sop, manual, work_order, inspection, incident, asset_registry, handover_note, regulation |
| source_path | string | relative path under data/sample_corpus |
| raw_text | text | normalized full text |
| created_at | datetime | |

## chunks
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| document_id | fk -> documents.id | |
| chunk_index | int | |
| text | text | |
| char_start | int | |
| char_end | int | |
| embedding | vector/float[] | pgvector column or JSON-encoded float list on SQLite |

## entities
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| entity_type | string | asset, person, failure_mode, work_order, incident, procedure, regulation, date |
| label | string | display text |
| ref_code | string\|null | e.g. WO-1043, IR-07, REG-014 |
| source_document_id | fk -> documents.id | first-seen document |

## relationships
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| source_entity_id | fk -> entities.id | |
| target_entity_id | fk -> entities.id | |
| relationship_type | string | asset->document, asset->work_order, asset->incident, incident->regulation, asset->procedure, work_order->failure_mode, inspection->compliance_gap, incident->incident |
| weight | float | similarity/strength where applicable |

## work_orders
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| wo_number | string | e.g. WO-1043 |
| asset_id | fk -> assets.id | |
| description | text | |
| failure_mode | string\|null | |
| status | string | open / closed |
| opened_at | datetime | |
| closed_at | datetime\|null | |

## incidents
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| incident_code | string | e.g. IR-07 |
| asset_id | fk -> assets.id | |
| title | string | |
| summary | text | |
| severity | string | low / medium / high |
| occurred_at | datetime | |

## inspections
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| asset_id | fk -> assets.id | |
| inspector | string | |
| checklist_item | string | |
| result | string | pass / fail / not_recorded |
| inspected_at | datetime | |

## regulations
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| code | string | e.g. REG-014 |
| title | string | |
| description | text | |

## compliance_gaps
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| asset_id | fk -> assets.id | |
| checklist_item | string | |
| regulation_id | fk -> regulations.id\|null | |
| status | string | ok / gap / at_risk |
| severity | string | low / medium / high |
| missing_evidence | text\|null | |
| corrective_action | text\|null | |

## lessons
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| incident_id | fk -> incidents.id | source incident |
| similar_incident_id | fk -> incidents.id | matched incident |
| similarity | float | 0-1 |
| warning_text | string | e.g. "resembles Incident IR-07 from last year" |

## recommendations
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| asset_id | fk -> assets.id | |
| action | string | |
| rationale | string | |
| priority | string | low / medium / high |

## benchmark_questions
| field | type | notes |
|---|---|---|
| id | string (uuid) | |
| question | string | |
| expected_document_ids | string[] | |
| expected_entity_ids | string[] | |
| expects_citation | bool | always true for this demo |
