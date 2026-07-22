// Shared TypeScript types mirroring schema.md and services/api/app/models.py.
// Keep in sync manually — this is a hackathon monorepo, not a codegen pipeline.

export type Criticality = "low" | "medium" | "high" | "critical";
export type Severity = "low" | "medium" | "high";
export type Priority = "low" | "medium" | "high";
export type ComplianceStatus = "ok" | "gap" | "at_risk";

export interface Asset {
  id: string;
  tag: string;
  name: string;
  asset_type: string;
  criticality: Criticality;
  location: string;
  risk_score: number;
  open_issues?: number;
}

export interface DocumentRef {
  id: string;
  title: string;
  doc_type: string;
  source_path?: string;
  created_at?: string;
}

export interface Citation {
  document_id: string;
  document_title: string;
  chunk_id: string;
  snippet: string;
}

export interface SupportingEntity {
  id: string;
  type: string;
  label: string;
}

export interface RecommendedAction {
  action: string;
  rationale: string;
  priority: Priority;
}

export interface CopilotAnswer {
  answer: string;
  confidence_score: number;
  citations: Citation[];
  supporting_entities: SupportingEntity[];
  supporting_documents: DocumentRef[];
  recommended_actions: RecommendedAction[];
}

export interface TimelineEvent {
  date: string;
  type: string;
  title: string;
  ref_id: string;
  summary: string;
}

export interface RecurringIssue {
  failure_mode: string;
  count: number;
  last_seen: string;
}

export interface SimilarIncident {
  incident_id: string;
  title: string;
  similarity: number;
  summary: string;
}

export interface ComplianceIssue {
  checklist_item: string;
  status: ComplianceStatus;
  severity: Severity;
}

export interface AssetThreeSixty {
  asset: Asset & { location: string };
  timeline: TimelineEvent[];
  recurring_issues: RecurringIssue[];
  similar_incidents: SimilarIncident[];
  compliance_issues: ComplianceIssue[];
  recommended_actions: RecommendedAction[];
  linked_documents: DocumentRef[];
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship_type: string;
  weight?: number;
}

export interface GraphNeighborhood {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ComplianceGap {
  id: string;
  asset_tag: string;
  checklist_item: string;
  regulation_ref?: string;
  status: ComplianceStatus;
  severity: Severity;
  missing_evidence?: string;
  corrective_action?: string;
}

export interface Lesson {
  incident_id: string;
  title: string;
  summary: string;
  similarity: number;
  date: string;
  warning: string;
}

export interface BenchmarkQuestion {
  id: string;
  question: string;
  expected_document_ids: string[];
  expected_entity_ids: string[];
  expects_citation: boolean;
}

export interface EvalRunResult {
  retrieval_hit_rate: number;
  citation_coverage: number;
  avg_latency_ms: number;
  entity_linkage_coverage: number;
  results: { question_id: string; passed: boolean; latency_ms: number }[];
}

export interface IngestionStatus {
  documents: number;
  chunks: number;
  entities: number;
  relationships: number;
  last_seeded_at: string | null;
}
