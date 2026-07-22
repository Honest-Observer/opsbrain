/**
 * Typed API client for OpsBrain, matching MASTER_SPEC.md §6 exactly.
 *
 * Hard requirement (MASTER_SPEC §13 / DECISIONS ADR-003): the UI must never break
 * because the backend is down or incomplete. Every exported function here tries the
 * real FastAPI backend first (http://localhost:8000/api by default) and, on any
 * failure (network error, non-2xx, timeout, bad shape), falls back to realistic
 * seeded mock data from ./mockData. Callers get an `ApiResult<T>` so the UI can show
 * a "Demo Mode" indicator when data is not live.
 */
import type {
  Asset,
  AssetThreeSixty,
  CopilotAnswer,
  GraphNeighborhood,
  ComplianceGap,
  Lesson,
  BenchmarkQuestion,
  EvalRunResult,
  IngestionStatus,
  DocumentRef,
} from "@shared/types";
import {
  MOCK_ASSETS,
  MOCK_DOCUMENTS,
  MOCK_INGESTION_STATUS,
  MOCK_COMPLIANCE_GAPS,
  MOCK_BENCHMARK_QUESTIONS,
  MOCK_EVAL_RESULT,
  getMockAssetThreeSixty,
  getMockCopilotAnswer,
  getMockGraphNeighborhood,
  getMockLessons,
  getMockDashboardAlerts,
  MOCK_REPEATED_ISSUES,
  type DashboardAlert,
  type RepeatedIssue,
} from "./mockData";

export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE as string | undefined) ?? "http://localhost:8000/api";

const DEFAULT_TIMEOUT_MS = 4000;
// Gemini-backed endpoints (copilot answer, seeding with real embeddings, the
// benchmark run) are much slower than a local call — a thinking-model answer can
// take 15-30s. Use a generous timeout for these so a live call isn't aborted and
// wrongly shown as "Demo Mode".
const SLOW_TIMEOUT_MS = 120000;

export interface ApiResult<T> {
  data: T;
  source: "live" | "mock";
  error?: string;
}

async function fetchJson<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

/** Wraps a live call + a mock fallback into a uniform ApiResult, per the
 * "demo never breaks" guardrail in MASTER_SPEC §13. */
async function withFallback<T>(
  path: string,
  init: RequestInit | undefined,
  mock: () => T,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<ApiResult<T>> {
  try {
    const data = await fetchJson<T>(path, init, timeoutMs);
    return { data, source: "live" };
  } catch (err) {
    return { data: mock(), source: "mock", error: err instanceof Error ? err.message : String(err) };
  }
}

// ---------------------------------------------------------------------------
// Health / backend status
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
  ai_mode?: "gemini" | "local";
  ai_model?: string;
  gemini_enabled?: boolean;
}

export async function checkHealth(): Promise<ApiResult<HealthResponse>> {
  return withFallback<HealthResponse>("/health", undefined, () => ({
    status: "mock",
    version: "0.0.0-mock",
    ai_mode: "local",
    ai_model: "local-heuristic",
    gemini_enabled: false,
  }));
}

// ---------------------------------------------------------------------------
// Upload (raw document ingestion) — multipart, so it bypasses fetchJson's
// JSON defaults. Returns the ingestion summary from POST /api/ingestion/upload.
// ---------------------------------------------------------------------------

export interface UploadResult {
  document_id: string;
  chunks_created: number;
  entities_created?: number;
  relationships_created?: number;
  ai_mode?: "gemini" | "local";
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/ingestion/upload`, { method: "POST", body: form });
  } catch (e) {
    throw new Error(
      `Could not reach the backend at ${API_BASE}. Is it running on :8000? (${e instanceof Error ? e.message : e})`
    );
  }
  if (!res.ok) {
    // Surface the real server-side reason (our error handler returns { detail }).
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return (await res.json()) as UploadResult;
}

// ---------------------------------------------------------------------------
// Ingestion
// ---------------------------------------------------------------------------

export interface SeedResponse {
  documents_ingested: number;
  chunks_created: number;
  entities_extracted: number;
  relationships_created: number;
}

export async function postIngestionSeed(): Promise<ApiResult<SeedResponse>> {
  return withFallback<SeedResponse>(
    "/ingestion/seed",
    { method: "POST" },
    () => ({
      documents_ingested: MOCK_INGESTION_STATUS.documents,
      chunks_created: MOCK_INGESTION_STATUS.chunks,
      entities_extracted: MOCK_INGESTION_STATUS.entities,
      relationships_created: MOCK_INGESTION_STATUS.relationships,
    }),
    SLOW_TIMEOUT_MS
  );
}

export async function getIngestionStatus(): Promise<ApiResult<IngestionStatus>> {
  return withFallback<IngestionStatus>("/ingestion/status", undefined, () => MOCK_INGESTION_STATUS);
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export async function getDocuments(): Promise<ApiResult<DocumentRef[]>> {
  return withFallback<DocumentRef[]>("/documents", undefined, () => MOCK_DOCUMENTS);
}

// ---------------------------------------------------------------------------
// Assets
// ---------------------------------------------------------------------------

export async function getAssets(): Promise<ApiResult<Asset[]>> {
  return withFallback<Asset[]>("/assets", undefined, () => MOCK_ASSETS);
}

export async function getAssetThreeSixty(id: string): Promise<ApiResult<AssetThreeSixty>> {
  return withFallback<AssetThreeSixty>(`/assets/${encodeURIComponent(id)}/three_sixty`, undefined, () =>
    getMockAssetThreeSixty(id)
  );
}

// ---------------------------------------------------------------------------
// Search / reasoning
// ---------------------------------------------------------------------------

export interface SemanticSearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  text: string;
  score: number;
}

export async function semanticSearch(q: string): Promise<ApiResult<SemanticSearchResult[]>> {
  return withFallback<SemanticSearchResult[]>(
    `/search/semantic?q=${encodeURIComponent(q)}`,
    undefined,
    () => [],
    SLOW_TIMEOUT_MS
  );
}

export async function getGraphNeighborhood(nodeId?: string, depth = 1): Promise<ApiResult<GraphNeighborhood>> {
  const qs = new URLSearchParams();
  if (nodeId) qs.set("node_id", nodeId);
  qs.set("depth", String(depth));
  return withFallback<GraphNeighborhood>(`/graph/neighborhood?${qs.toString()}`, undefined, () =>
    getMockGraphNeighborhood(nodeId, depth)
  );
}

export async function postCopilotAsk(question: string): Promise<ApiResult<CopilotAnswer>> {
  return withFallback<CopilotAnswer>(
    "/copilot/ask",
    { method: "POST", body: JSON.stringify({ question }) },
    () => getMockCopilotAnswer(question),
    SLOW_TIMEOUT_MS
  );
}

// ---------------------------------------------------------------------------
// Compliance
// ---------------------------------------------------------------------------

export async function getComplianceGaps(): Promise<ApiResult<ComplianceGap[]>> {
  return withFallback<ComplianceGap[]>("/compliance/gaps", undefined, () => MOCK_COMPLIANCE_GAPS);
}

export interface EvidencePack {
  asset_id: string;
  asset_tag: string;
  asset_name: string;
  generated_at: string;
  compliance_gaps: ComplianceGap[];
  linked_documents: DocumentRef[];
  supporting_entities: { id: string; type: string; label: string }[];
}

export async function getEvidencePack(assetId: string, assetTag?: string): Promise<ApiResult<EvidencePack>> {
  return withFallback<EvidencePack>(`/compliance/evidence_pack/${encodeURIComponent(assetId)}`, undefined, () => ({
    asset_id: assetId,
    asset_tag: assetTag ?? assetId,
    asset_name: assetTag ?? assetId,
    generated_at: new Date().toISOString(),
    compliance_gaps: MOCK_COMPLIANCE_GAPS.filter((g) => !assetTag || g.asset_tag === assetTag),
    linked_documents: MOCK_DOCUMENTS.slice(0, 5),
    supporting_entities: [{ id: `asset:${assetId}`, type: "asset", label: assetTag ?? assetId }],
  }));
}

// ---------------------------------------------------------------------------
// Lessons learned
// ---------------------------------------------------------------------------

export async function getLessons(assetId?: string): Promise<ApiResult<Lesson[]>> {
  const qs = assetId ? `?asset_id=${encodeURIComponent(assetId)}` : "";
  return withFallback<Lesson[]>(`/lessons${qs}`, undefined, () => getMockLessons(assetId));
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------

export async function getEvalQuestions(): Promise<ApiResult<BenchmarkQuestion[]>> {
  return withFallback<BenchmarkQuestion[]>("/eval/questions", undefined, () => MOCK_BENCHMARK_QUESTIONS);
}

export async function postEvalRun(): Promise<ApiResult<EvalRunResult>> {
  return withFallback<EvalRunResult>("/eval/run", { method: "POST" }, () => MOCK_EVAL_RESULT, SLOW_TIMEOUT_MS);
}

// ---------------------------------------------------------------------------
// Dashboard (composed client-side — MASTER_SPEC §6 has no single dashboard
// endpoint, so this aggregates /assets, /assets/{id}/three_sixty and
// /compliance/gaps, which works identically against the live backend or mocks)
// ---------------------------------------------------------------------------

export interface DashboardData {
  ingestion: IngestionStatus;
  topRiskyAssets: Asset[];
  alerts: DashboardAlert[];
  repeatedIssues: RepeatedIssue[];
}

export async function getDashboardData(): Promise<ApiResult<DashboardData>> {
  const [ingestionRes, assetsRes, gapsRes] = await Promise.all([
    getIngestionStatus(),
    getAssets(),
    getComplianceGaps(),
  ]);

  const anyMock = ingestionRes.source === "mock" || assetsRes.source === "mock" || gapsRes.source === "mock";

  const topRiskyAssets = [...assetsRes.data].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);

  // Alerts derived from high/medium severity compliance gaps, real or mock alike.
  const gapAlerts: DashboardAlert[] = gapsRes.data
    .filter((g) => g.status !== "ok")
    .sort((a, b) => severityRank(b.severity) - severityRank(a.severity))
    .slice(0, 6)
    .map((g) => ({
      id: g.id,
      severity: g.severity,
      title: `${g.asset_tag} — ${g.checklist_item}`,
      detail: g.missing_evidence ?? g.corrective_action ?? "Compliance gap flagged.",
      assetTag: g.asset_tag,
    }));

  // Aggregate recurring issues from the top 3 riskiest assets' 360 views — real
  // endpoint calls either way, so this works whether the backend is live or mocked.
  const top3 = topRiskyAssets.slice(0, 3);
  const three60s = await Promise.all(top3.map((a) => getAssetThreeSixty(a.id)));
  const issueMap = new Map<string, RepeatedIssue>();
  for (const r of three60s) {
    for (const issue of r.data.recurring_issues) {
      const existing = issueMap.get(issue.failure_mode);
      if (existing) {
        existing.count = Math.max(existing.count, issue.count);
      } else {
        issueMap.set(issue.failure_mode, {
          failure_mode: issue.failure_mode,
          count: issue.count,
          assets_affected: [r.data.asset.tag],
        });
      }
    }
  }
  const repeatedIssues = issueMap.size > 0 ? Array.from(issueMap.values()) : MOCK_REPEATED_ISSUES;

  const alerts = gapAlerts.length > 0 ? gapAlerts : getMockDashboardAlerts();

  return {
    data: {
      ingestion: ingestionRes.data,
      topRiskyAssets,
      alerts,
      repeatedIssues,
    },
    source: anyMock ? "mock" : "live",
  };
}

function severityRank(s: "low" | "medium" | "high"): number {
  return s === "high" ? 2 : s === "medium" ? 1 : 0;
}
