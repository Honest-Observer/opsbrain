/**
 * Seeded, cross-referenced mock data for OpsBrain.
 *
 * This is the "demo never breaks" safety net described in MASTER_SPEC.md §13:
 * every api.ts function falls back to something from this file if the real
 * backend (services/api, FastAPI on :8000) is unreachable or incomplete.
 *
 * All ids/tags here are deliberately cross-referenced (P-101 <-> IR-07 <-> WO-1042
 * <-> SOP-CENT-PUMP-01 etc.) so every screen tells the *same* coherent plant story
 * per the demo flow in MASTER_SPEC.md §11, not disconnected placeholder rows.
 */
import type {
  Asset,
  DocumentRef,
  AssetThreeSixty,
  CopilotAnswer,
  GraphNode,
  GraphEdge,
  GraphNeighborhood,
  ComplianceGap,
  Lesson,
  BenchmarkQuestion,
  EvalRunResult,
  IngestionStatus,
} from "@shared/types";

// ---------------------------------------------------------------------------
// Assets
// ---------------------------------------------------------------------------

export const MOCK_ASSETS: Asset[] = [
  {
    id: "P-101",
    tag: "P-101",
    name: "Centrifugal Feed Pump",
    asset_type: "Pump",
    criticality: "high",
    location: "Pump House 2",
    risk_score: 88,
    open_issues: 4,
  },
  {
    id: "B-12",
    tag: "B-12",
    name: "Package Boiler",
    asset_type: "Boiler",
    criticality: "critical",
    location: "Utilities Block",
    risk_score: 92,
    open_issues: 3,
  },
  {
    id: "CP-303",
    tag: "CP-303",
    name: "Reciprocating Compressor",
    asset_type: "Compressor",
    criticality: "high",
    location: "Compressor House",
    risk_score: 73,
    open_issues: 2,
  },
  {
    id: "TX-450",
    tag: "TX-450",
    name: "Step-Up Transformer",
    asset_type: "Transformer",
    criticality: "high",
    location: "Substation A",
    risk_score: 67,
    open_issues: 2,
  },
  {
    id: "CV-220",
    tag: "CV-220",
    name: "Belt Conveyor",
    asset_type: "Conveyor",
    criticality: "medium",
    location: "Material Handling",
    risk_score: 54,
    open_issues: 1,
  },
  {
    id: "HX-08",
    tag: "HX-08",
    name: "Shell & Tube Heat Exchanger",
    asset_type: "Heat Exchanger",
    criticality: "medium",
    location: "Process Unit 3",
    risk_score: 41,
    open_issues: 1,
  },
];

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export const MOCK_DOCUMENTS: DocumentRef[] = [
  { id: "SOP-CENT-PUMP-01", title: "Centrifugal Pump Operating & Maintenance SOP", doc_type: "sop", source_path: "data/sample_corpus/sops/SOP-CENT-PUMP-01.md", created_at: "2024-02-01" },
  { id: "OEM-P101-MANUAL", title: "P-101 OEM Manual — XYZ Pumps Model CX-500", doc_type: "manual", source_path: "data/sample_corpus/manuals/OEM-P101-MANUAL.pdf", created_at: "2023-11-14" },
  { id: "WO-1042", title: "Work Order: Mechanical Seal Replacement — P-101", doc_type: "work_order", source_path: "data/sample_corpus/work_orders/WO-1042.txt", created_at: "2026-07-05" },
  { id: "WO-1058", title: "Work Order: Bearing Vibration Alarm — P-101", doc_type: "work_order", source_path: "data/sample_corpus/work_orders/WO-1058.txt", created_at: "2026-05-02" },
  { id: "WO-1071", title: "Work Order: Seal Leak Repair — P-101", doc_type: "work_order", source_path: "data/sample_corpus/work_orders/WO-1071.txt", created_at: "2026-06-21" },
  { id: "IR-07", title: "Incident Report: P-101 Seal Failure & Minor Process Leak", doc_type: "incident", source_path: "data/sample_corpus/incidents/IR-07.md", created_at: "2026-06-19" },
  { id: "IR-11", title: "Incident Report: P-101 Bearing Overheat Trip", doc_type: "incident", source_path: "data/sample_corpus/incidents/IR-11.md", created_at: "2025-11-02" },
  { id: "SHIFT-HANDOVER-0619", title: "Shift Handover Notes — Night Shift 19 Jun", doc_type: "handover", source_path: "data/sample_corpus/handovers/SHIFT-HANDOVER-0619.txt", created_at: "2026-06-19" },
  { id: "INSPECTION-B12-Q2", title: "Boiler B-12 Quarterly Pressure Vessel Inspection Report", doc_type: "inspection", source_path: "data/sample_corpus/inspections/INSPECTION-B12-Q2.csv", created_at: "2026-06-30" },
  { id: "REG-OSHA-301", title: "OSHA 301 — Pressure Vessel Safety Checklist", doc_type: "regulation", source_path: "data/sample_corpus/regulations/REG-OSHA-301.md", created_at: "2022-01-01" },
  { id: "REG-089", title: "Internal Standard REG-089 — Boiler Relief Valve Testing", doc_type: "regulation", source_path: "data/sample_corpus/regulations/REG-089.md", created_at: "2022-06-01" },
  { id: "SOP-BOILER-12", title: "Boiler B-12 Operating SOP", doc_type: "sop", source_path: "data/sample_corpus/sops/SOP-BOILER-12.md", created_at: "2024-03-10" },
  { id: "ASSET-REGISTRY", title: "Plant Asset Registry Export", doc_type: "registry", source_path: "data/sample_corpus/registry/ASSET-REGISTRY.xlsx", created_at: "2026-01-01" },
  { id: "WO-2004", title: "Work Order: Belt Tracking Adjustment — CV-220", doc_type: "work_order", source_path: "data/sample_corpus/work_orders/WO-2004.txt", created_at: "2026-04-18" },
  { id: "IR-14", title: "Incident Report: CV-220 Belt Slip Near-Miss", doc_type: "incident", source_path: "data/sample_corpus/incidents/IR-14.md", created_at: "2026-04-19" },
  { id: "INSPECTION-TX450", title: "Transformer TX-450 Annual Insulation Test Report", doc_type: "inspection", source_path: "data/sample_corpus/inspections/INSPECTION-TX450.csv", created_at: "2026-03-01" },
];

// ---------------------------------------------------------------------------
// Asset 360
// ---------------------------------------------------------------------------

const ASSET_360: Record<string, AssetThreeSixty> = {
  "P-101": {
    asset: { ...MOCK_ASSETS[0], location: "Pump House 2" },
    timeline: [
      { date: "2025-04-10", type: "work_order", title: "Mechanical seal replaced (OEM spec)", ref_id: "WO-0988", summary: "Routine seal replacement during scheduled shutdown." },
      { date: "2025-11-02", type: "incident", title: "Bearing overheat trip", ref_id: "IR-11", summary: "High bearing temperature alarm tripped pump on high-high setpoint; root cause traced to lubrication starvation." },
      { date: "2026-02-14", type: "inspection", title: "Routine vibration inspection — elevated readings", ref_id: "INSP-P101-Q1", summary: "Vibration trending up on outboard bearing; flagged for monitoring." },
      { date: "2026-05-02", type: "work_order", title: "Bearing vibration alarm investigated", ref_id: "WO-1058", summary: "Vibration alarm re-triggered; bearing replaced, alignment corrected." },
      { date: "2026-06-19", type: "incident", title: "Seal failure & minor process leak", ref_id: "IR-07", summary: "Mechanical seal failed under low-flow operation, minor process fluid leak contained, no injuries." },
      { date: "2026-06-21", type: "work_order", title: "Seal leak repair", ref_id: "WO-1071", summary: "Emergency seal repair performed; interim fix pending permanent cartridge seal upgrade." },
      { date: "2026-07-05", type: "work_order", title: "Cartridge seal upgrade trial (API 682 Plan 53B)", ref_id: "WO-1042", summary: "Upgraded mechanical seal to cartridge design with dual-pressure barrier fluid system." },
    ],
    recurring_issues: [
      { failure_mode: "Mechanical seal leakage", count: 4, last_seen: "2026-06-19" },
      { failure_mode: "Bearing overheating", count: 2, last_seen: "2026-05-02" },
    ],
    similar_incidents: [
      { incident_id: "IR-11", title: "P-101 Bearing Overheat Trip", similarity: 0.78, summary: "Same asset, related lubrication/thermal root cause cluster." },
      { incident_id: "IR-19", title: "P-104 Seal Failure Under Low-Flow Operation", similarity: 0.65, summary: "Sister pump on Train B failed for the same low-flow cavitation reason." },
    ],
    compliance_issues: [
      { checklist_item: "Lockout-Tagout Verification Log", status: "gap", severity: "medium" },
      { checklist_item: "Confined Space Entry Permit", status: "ok", severity: "low" },
    ],
    recommended_actions: [
      { action: "Replace mechanical seal with upgraded cartridge seal (API 682 Plan 53B)", rationale: "4 recurring seal failures in 14 months correlate with cavitation at low-flow operation; cartridge seal with barrier fluid addresses root cause rather than symptom.", priority: "high" },
      { action: "Add minimum-flow interlock to control logic", rationale: "Every seal failure on record occurred while the pump ran below its minimum continuous stable flow.", priority: "high" },
      { action: "Schedule quarterly vibration analysis", rationale: "Bearing failures were preceded by a detectable vibration trend that was only caught after an alarm, not proactively.", priority: "medium" },
    ],
    linked_documents: [
      { id: "SOP-CENT-PUMP-01", title: "Centrifugal Pump Operating & Maintenance SOP", doc_type: "sop" },
      { id: "OEM-P101-MANUAL", title: "P-101 OEM Manual — XYZ Pumps Model CX-500", doc_type: "manual" },
      { id: "WO-1042", title: "Work Order: Mechanical Seal Replacement — P-101", doc_type: "work_order" },
      { id: "WO-1058", title: "Work Order: Bearing Vibration Alarm — P-101", doc_type: "work_order" },
      { id: "WO-1071", title: "Work Order: Seal Leak Repair — P-101", doc_type: "work_order" },
      { id: "IR-07", title: "Incident Report: P-101 Seal Failure & Minor Process Leak", doc_type: "incident" },
      { id: "IR-11", title: "Incident Report: P-101 Bearing Overheat Trip", doc_type: "incident" },
      { id: "SHIFT-HANDOVER-0619", title: "Shift Handover Notes — Night Shift 19 Jun", doc_type: "handover" },
    ],
  },
  "B-12": {
    asset: { ...MOCK_ASSETS[1], location: "Utilities Block" },
    timeline: [
      { date: "2025-06-01", type: "inspection", title: "Annual pressure vessel inspection — passed", ref_id: "INSP-B12-2025", summary: "Routine annual inspection, no findings." },
      { date: "2026-01-15", type: "work_order", title: "Relief valve set-point drift corrected", ref_id: "WO-1890", summary: "Relief valve found drifting below set point; recalibrated." },
      { date: "2026-04-20", type: "incident", title: "Low-water cutoff test failure", ref_id: "IR-03", summary: "Scheduled low-water cutoff functional test failed on first attempt; passed on retest after cleaning probe." },
      { date: "2026-06-30", type: "inspection", title: "Quarterly pressure vessel inspection", ref_id: "INSPECTION-B12-Q2", summary: "Inspection completed; relief valve test certificate not on file, flagged as compliance gap." },
    ],
    recurring_issues: [
      { failure_mode: "Relief valve set-point drift", count: 3, last_seen: "2026-01-15" },
    ],
    similar_incidents: [
      { incident_id: "IR-03", title: "B-12 Low-Water Cutoff Test Failure", similarity: 0.55, summary: "Same asset, instrumentation drift pattern." },
    ],
    compliance_issues: [
      { checklist_item: "Pressure Relief Valve Test Certificate", status: "gap", severity: "high" },
      { checklist_item: "Quarterly Inspection Evidence", status: "at_risk", severity: "medium" },
    ],
    recommended_actions: [
      { action: "Commission third-party relief valve test before next quarter", rationale: "No certified test certificate on file since 2024-11; this is a hard regulatory requirement under REG-089.", priority: "high" },
      { action: "File missing OSHA 301 checklist evidence", rationale: "Checklist was signed but inspector countersignature is missing, blocking audit close-out.", priority: "high" },
    ],
    linked_documents: [
      { id: "INSPECTION-B12-Q2", title: "Boiler B-12 Quarterly Pressure Vessel Inspection Report", doc_type: "inspection" },
      { id: "REG-OSHA-301", title: "OSHA 301 — Pressure Vessel Safety Checklist", doc_type: "regulation" },
      { id: "REG-089", title: "Internal Standard REG-089 — Boiler Relief Valve Testing", doc_type: "regulation" },
      { id: "SOP-BOILER-12", title: "Boiler B-12 Operating SOP", doc_type: "sop" },
      { id: "ASSET-REGISTRY", title: "Plant Asset Registry Export", doc_type: "registry" },
    ],
  },
};

/** Generic, still-plausible Asset 360 for any asset id not hand-authored above. */
function genericAssetThreeSixty(id: string): AssetThreeSixty {
  const asset = MOCK_ASSETS.find((a) => a.id === id || a.tag === id) ?? {
    id,
    tag: id,
    name: `Unregistered Asset ${id}`,
    asset_type: "Unknown",
    criticality: "medium" as const,
    location: "Unassigned",
    risk_score: 30,
    open_issues: 0,
  };
  return {
    asset: { ...asset, location: asset.location },
    timeline: [
      { date: "2026-02-01", type: "inspection", title: `Routine inspection — ${asset.tag}`, ref_id: `INSP-${asset.tag}`, summary: "No abnormal findings recorded." },
      { date: "2026-05-11", type: "work_order", title: `Preventive maintenance — ${asset.tag}`, ref_id: `WO-${asset.tag}-PM`, summary: "Standard preventive maintenance completed on schedule." },
    ],
    recurring_issues: [],
    similar_incidents: [],
    compliance_issues: [{ checklist_item: "Standard PM Checklist", status: "ok", severity: "low" }],
    recommended_actions: [
      { action: "Continue standard preventive maintenance cadence", rationale: "No recurring failure pattern detected for this asset in the current corpus.", priority: "low" },
    ],
    linked_documents: [{ id: "ASSET-REGISTRY", title: "Plant Asset Registry Export", doc_type: "registry" }],
  };
}

export function getMockAssetThreeSixty(id: string): AssetThreeSixty {
  return ASSET_360[id] ?? genericAssetThreeSixty(id);
}

// ---------------------------------------------------------------------------
// Copilot
// ---------------------------------------------------------------------------

export const DEMO_QUERIES: string[] = [
  "Why is Pump P-101 repeatedly failing?",
  "Show compliance gaps affecting Boiler B-12",
  "What past incidents resemble this issue?",
  "What should we do before the next shutdown on P-101?",
  "Which assets have the highest unaddressed risk right now?",
];

function copilotAnswerForP101(): CopilotAnswer {
  return {
    answer:
      "P-101 has failed 4 times in the last 14 months due to recurring mechanical seal leakage (IR-07, plus 3 prior work orders), with a secondary bearing-overheat pattern (IR-11, WO-1058). All seal failures occurred while the pump was operating below its minimum continuous stable flow, which causes internal recirculation and cavitation at the seal faces. The current seal is a single-spring design without a flush plan suited for low-flow excursions. Recommended fix: upgrade to a cartridge seal with an API 682 Plan 53B barrier-fluid system and add a minimum-flow interlock so the pump cannot run in the failure-prone regime.",
    confidence_score: 0.87,
    citations: [
      { document_id: "IR-07", document_title: "Incident Report: P-101 Seal Failure & Minor Process Leak", chunk_id: "IR-07#c2", snippet: "Seal failure occurred approximately 40 minutes after flow dropped below 60 gpm, consistent with prior low-flow related failures on this unit." },
      { document_id: "WO-1042", document_title: "Work Order: Mechanical Seal Replacement — P-101", chunk_id: "WO-1042#c1", snippet: "Replaced single mechanical seal with cartridge seal, API 682 Plan 53B, as trial mitigation per reliability engineering recommendation." },
      { document_id: "SOP-CENT-PUMP-01", document_title: "Centrifugal Pump Operating & Maintenance SOP", chunk_id: "SOP-CENT-PUMP-01#c4", snippet: "Operators must not run pump below minimum continuous stable flow (85 gpm) for more than 5 minutes to avoid seal and bearing damage." },
      { document_id: "IR-11", document_title: "Incident Report: P-101 Bearing Overheat Trip", chunk_id: "IR-11#c1", snippet: "Bearing temperature exceeded high-high setpoint; lubrication starvation suspected, secondary to prolonged low-flow operation." },
    ],
    supporting_entities: [
      { id: "asset:P-101", type: "asset", label: "P-101 — Centrifugal Feed Pump" },
      { id: "failure_mode:mechanical_seal_leak", type: "failure_mode", label: "Mechanical seal leakage" },
      { id: "failure_mode:bearing_overheat", type: "failure_mode", label: "Bearing overheating" },
      { id: "incident:IR-07", type: "incident", label: "IR-07 — Seal Failure & Minor Process Leak" },
      { id: "incident:IR-11", type: "incident", label: "IR-11 — Bearing Overheat Trip" },
    ],
    supporting_documents: [
      { id: "IR-07", title: "Incident Report: P-101 Seal Failure & Minor Process Leak", doc_type: "incident" },
      { id: "WO-1042", title: "Work Order: Mechanical Seal Replacement — P-101", doc_type: "work_order" },
      { id: "SOP-CENT-PUMP-01", title: "Centrifugal Pump Operating & Maintenance SOP", doc_type: "sop" },
      { id: "IR-11", title: "Incident Report: P-101 Bearing Overheat Trip", doc_type: "incident" },
    ],
    recommended_actions: [
      { action: "Upgrade to cartridge mechanical seal with API 682 Plan 53B barrier fluid", rationale: "Directly addresses the low-flow cavitation root cause behind all 4 recorded seal failures.", priority: "high" },
      { action: "Add minimum-flow interlock (85 gpm) to control logic", rationale: "Every failure on record occurred during sustained low-flow operation that the SOP already prohibits but nothing currently enforces.", priority: "high" },
      { action: "Schedule quarterly vibration analysis on bearings", rationale: "Bearing overheat trip in IR-11 was preceded by a detectable vibration trend.", priority: "medium" },
    ],
  };
}

function copilotAnswerForB12(): CopilotAnswer {
  return {
    answer:
      "Boiler B-12 currently has two open compliance gaps. The Pressure Relief Valve Test Certificate (required annually under REG-089) has not been on file since November 2024 — this is a high-severity gap because it blocks legal operation past the next audit window. The OSHA 301 Pressure Vessel Safety Checklist was completed but is missing the inspector's countersignature, which is a medium-severity procedural gap. Recommended next step is to commission a certified relief-valve test immediately and route the OSHA 301 checklist back to the inspector for countersignature.",
    confidence_score: 0.81,
    citations: [
      { document_id: "INSPECTION-B12-Q2", document_title: "Boiler B-12 Quarterly Pressure Vessel Inspection Report", chunk_id: "INSPECTION-B12-Q2#c1", snippet: "Relief valve test certificate not found in maintenance records; last certificate on file dated 2024-11-08." },
      { document_id: "REG-089", document_title: "Internal Standard REG-089 — Boiler Relief Valve Testing", chunk_id: "REG-089#c1", snippet: "Pressure relief valves on Class II vessels shall be certified-tested at intervals not exceeding 12 months." },
      { document_id: "REG-OSHA-301", document_title: "OSHA 301 — Pressure Vessel Safety Checklist", chunk_id: "REG-OSHA-301#c3", snippet: "Checklist requires inspector countersignature prior to filing as compliant evidence." },
    ],
    supporting_entities: [
      { id: "asset:B-12", type: "asset", label: "B-12 — Package Boiler" },
      { id: "reg:REG-089", type: "regulation", label: "REG-089 — Relief Valve Testing Standard" },
      { id: "reg:OSHA-301", type: "regulation", label: "OSHA 301 — Pressure Vessel Checklist" },
    ],
    supporting_documents: [
      { id: "INSPECTION-B12-Q2", title: "Boiler B-12 Quarterly Pressure Vessel Inspection Report", doc_type: "inspection" },
      { id: "REG-089", title: "Internal Standard REG-089 — Boiler Relief Valve Testing", doc_type: "regulation" },
    ],
    recommended_actions: [
      { action: "Commission third-party relief valve test before next quarter", rationale: "No certified test certificate on file since 2024-11; hard regulatory requirement under REG-089.", priority: "high" },
      { action: "Route OSHA 301 checklist to inspector for countersignature", rationale: "Checklist is otherwise complete; missing signature is the only blocker to audit close-out.", priority: "medium" },
    ],
  };
}

function copilotAnswerGeneric(question: string): CopilotAnswer {
  return {
    answer:
      `Based on the seeded demo corpus, here is a general synthesis for: "${question}". OpsBrain retrieves the most relevant chunks across SOPs, work orders, incident reports, and regulations, then grounds its answer in the citations below. Ask about a specific asset tag (e.g. P-101, B-12, CP-303, TX-450, CV-220, HX-08) for a much more targeted, cited answer.`,
    confidence_score: 0.52,
    citations: [
      { document_id: "ASSET-REGISTRY", document_title: "Plant Asset Registry Export", chunk_id: "ASSET-REGISTRY#c1", snippet: "Plant asset registry lists 6 tracked assets across pumps, boilers, compressors, transformers, conveyors, and heat exchangers." },
    ],
    supporting_entities: [{ id: "asset:P-101", type: "asset", label: "P-101 — Centrifugal Feed Pump" }],
    supporting_documents: [{ id: "ASSET-REGISTRY", title: "Plant Asset Registry Export", doc_type: "asset_registry" }],
    recommended_actions: [
      { action: "Ask a more specific question referencing an asset tag or incident ID", rationale: "Narrower questions retrieve more precise, higher-confidence citations from the knowledge graph.", priority: "low" },
    ],
  };
}

export function getMockCopilotAnswer(question: string): CopilotAnswer {
  const q = question.toLowerCase();
  if (q.includes("p-101") || q.includes("p101") || (q.includes("pump") && q.includes("fail"))) {
    return copilotAnswerForP101();
  }
  if (q.includes("b-12") || q.includes("b12") || q.includes("boiler")) {
    return copilotAnswerForB12();
  }
  return copilotAnswerGeneric(question);
}

// ---------------------------------------------------------------------------
// Compliance gaps
// ---------------------------------------------------------------------------

export const MOCK_COMPLIANCE_GAPS: ComplianceGap[] = [
  { id: "gap-1", asset_tag: "B-12", checklist_item: "Pressure Relief Valve Test Certificate", regulation_ref: "REG-089", status: "gap", severity: "high", missing_evidence: "No test certificate on file since 2024-11-08.", corrective_action: "Schedule certified relief valve test and upload certificate." },
  { id: "gap-2", asset_tag: "B-12", checklist_item: "OSHA 301 Pressure Vessel Checklist", regulation_ref: "OSHA-301", status: "at_risk", severity: "medium", missing_evidence: "Checklist signed but missing inspector countersignature.", corrective_action: "Obtain inspector countersignature and re-file." },
  { id: "gap-3", asset_tag: "P-101", checklist_item: "Lockout-Tagout Verification Log", regulation_ref: "REG-045", status: "gap", severity: "medium", missing_evidence: "LOTO log not updated after WO-1071 seal repair.", corrective_action: "Backfill LOTO log entries and retrain shift crew." },
  { id: "gap-4", asset_tag: "TX-450", checklist_item: "Insulation Resistance Test Record", regulation_ref: "REG-112", status: "ok", severity: "low" },
  { id: "gap-5", asset_tag: "CP-303", checklist_item: "Confined Space Entry Permit", regulation_ref: "OSHA-146", status: "gap", severity: "high", missing_evidence: "No permit on file for last compressor overhaul.", corrective_action: "File retroactive permit and add to PM checklist template." },
  { id: "gap-6", asset_tag: "CV-220", checklist_item: "Guarding Inspection Log", regulation_ref: "REG-077", status: "at_risk", severity: "low", missing_evidence: "Inspection overdue by 12 days.", corrective_action: "Complete guarding inspection this week." },
  { id: "gap-7", asset_tag: "HX-08", checklist_item: "Tube Bundle Cleaning Record", regulation_ref: "REG-063", status: "ok", severity: "low" },
];

// ---------------------------------------------------------------------------
// Lessons learned
// ---------------------------------------------------------------------------

export const MOCK_LESSONS: Lesson[] = [
  { incident_id: "IR-07", title: "P-101 Seal Failure & Minor Process Leak", summary: "Mechanical seal failed under sustained low-flow operation.", similarity: 1.0, date: "2026-06-19", warning: "Resembles a recurring pattern: seal failures cluster after low-flow excursions. Inspect seal flush plan before the next low-flow window." },
  { incident_id: "IR-11", title: "P-101 Bearing Overheat Trip", summary: "Bearing overheated after prolonged low-flow operation caused lubrication starvation.", similarity: 0.78, date: "2025-11-02", warning: "Same root-cause family as IR-07 (low-flow operation on P-101) — proactively schedule vibration analysis before the next scheduled turnaround." },
  { incident_id: "IR-19", title: "P-104 Seal Failure Under Low-Flow Operation", summary: "Sister pump on Train B failed for the same low-flow cavitation reason as P-101.", similarity: 0.65, date: "2026-03-08", warning: "Cross-asset pattern: any centrifugal pump lacking a minimum-flow interlock is at risk. Consider a fleet-wide interlock retrofit, not just P-101." },
  { incident_id: "IR-03", title: "B-12 Low-Water Cutoff Test Failure", summary: "Scheduled low-water cutoff functional test failed on first attempt.", similarity: 0.55, date: "2026-04-20", warning: "Instrumentation drift pattern on B-12 — pair with the open relief-valve test certificate gap for a single combined corrective action visit." },
  { incident_id: "IR-14", title: "CV-220 Belt Slip Near-Miss", summary: "Belt tracking drift nearly caused a material spill near a walkway.", similarity: 0.4, date: "2026-04-19", warning: "Guarding inspection on CV-220 is currently overdue — this near-miss plus the open gap together raise urgency." },
  { incident_id: "IR-22", title: "CP-303 Valve Wear Trip", summary: "Compressor tripped on high discharge temperature due to worn suction valve.", similarity: 0.35, date: "2025-09-12", warning: "Confined space entry permit for CP-303 overhauls is currently missing — the next overhaul should not proceed until that gap is closed." },
];

export function getMockLessons(assetId?: string): Lesson[] {
  if (!assetId) return MOCK_LESSONS;
  const assetIncidentMap: Record<string, string[]> = {
    "P-101": ["IR-07", "IR-11", "IR-19"],
    "B-12": ["IR-03"],
    "CV-220": ["IR-14"],
    "CP-303": ["IR-22"],
  };
  const ids = assetIncidentMap[assetId];
  if (!ids) return MOCK_LESSONS;
  return MOCK_LESSONS.filter((l) => ids.includes(l.incident_id));
}

// ---------------------------------------------------------------------------
// Ingestion status
// ---------------------------------------------------------------------------

export const MOCK_INGESTION_STATUS: IngestionStatus = {
  documents: 16,
  chunks: 214,
  entities: 138,
  relationships: 261,
  last_seeded_at: "2026-07-20T09:14:00Z",
};

// ---------------------------------------------------------------------------
// Evaluation / benchmark
// ---------------------------------------------------------------------------

export const MOCK_BENCHMARK_QUESTIONS: BenchmarkQuestion[] = [
  { id: "q1", question: "Why does Pump P-101 keep failing?", expected_document_ids: ["IR-07", "WO-1042", "IR-11"], expected_entity_ids: ["asset:P-101", "failure_mode:mechanical_seal_leak"], expects_citation: true },
  { id: "q2", question: "What compliance gaps affect Boiler B-12?", expected_document_ids: ["INSPECTION-B12-Q2", "REG-089"], expected_entity_ids: ["asset:B-12", "reg:REG-089"], expects_citation: true },
  { id: "q3", question: "What incidents resemble IR-07?", expected_document_ids: ["IR-11", "IR-19"], expected_entity_ids: ["incident:IR-07"], expects_citation: true },
  { id: "q4", question: "What is the minimum continuous stable flow for P-101?", expected_document_ids: ["SOP-CENT-PUMP-01"], expected_entity_ids: ["asset:P-101"], expects_citation: true },
  { id: "q5", question: "When was B-12's last relief valve test certificate filed?", expected_document_ids: ["INSPECTION-B12-Q2"], expected_entity_ids: ["asset:B-12"], expects_citation: true },
  { id: "q6", question: "What caused the CV-220 belt slip near-miss?", expected_document_ids: ["IR-14", "WO-2004"], expected_entity_ids: ["asset:CV-220"], expects_citation: true },
  { id: "q7", question: "What work was done on P-101 in July 2026?", expected_document_ids: ["WO-1042"], expected_entity_ids: ["asset:P-101"], expects_citation: true },
  { id: "q8", question: "Which regulation governs boiler relief valve testing?", expected_document_ids: ["REG-089"], expected_entity_ids: ["reg:REG-089"], expects_citation: true },
  { id: "q9", question: "What is the recommended fix for P-101 seal failures?", expected_document_ids: ["WO-1042", "IR-07"], expected_entity_ids: ["asset:P-101", "failure_mode:mechanical_seal_leak"], expects_citation: true },
  { id: "q10", question: "Is TX-450's insulation resistance test current?", expected_document_ids: ["INSPECTION-TX450"], expected_entity_ids: ["asset:TX-450"], expects_citation: true },
  { id: "q11", question: "What OSHA checklist applies to pressure vessels?", expected_document_ids: ["REG-OSHA-301"], expected_entity_ids: ["reg:OSHA-301"], expects_citation: true },
  { id: "q12", question: "What is CP-303's confined space entry permit status?", expected_document_ids: ["ASSET-REGISTRY"], expected_entity_ids: ["asset:CP-303"], expects_citation: true },
  { id: "q13", question: "Summarize the P-101 bearing overheat incident.", expected_document_ids: ["IR-11"], expected_entity_ids: ["asset:P-101", "failure_mode:bearing_overheat"], expects_citation: true },
  { id: "q14", question: "What does the shift handover note from 19 June say about P-101?", expected_document_ids: ["SHIFT-HANDOVER-0619"], expected_entity_ids: ["asset:P-101"], expects_citation: true },
  { id: "q15", question: "What is the OEM spec for P-101's seal?", expected_document_ids: ["OEM-P101-MANUAL"], expected_entity_ids: ["asset:P-101"], expects_citation: true },
  { id: "q16", question: "How many times has B-12's relief valve drifted out of set point?", expected_document_ids: ["INSPECTION-B12-Q2"], expected_entity_ids: ["asset:B-12"], expects_citation: true },
  { id: "q17", question: "What corrective action closes the CP-303 confined space gap?", expected_document_ids: ["ASSET-REGISTRY"], expected_entity_ids: ["asset:CP-303"], expects_citation: true },
  { id: "q18", question: "What SOP governs B-12 operation?", expected_document_ids: ["SOP-BOILER-12"], expected_entity_ids: ["asset:B-12"], expects_citation: true },
  { id: "q19", question: "What is the risk score trend for the plant's most critical assets?", expected_document_ids: ["ASSET-REGISTRY"], expected_entity_ids: ["asset:B-12", "asset:P-101"], expects_citation: true },
  { id: "q20", question: "What near-miss occurred on CV-220 and what is the guarding status?", expected_document_ids: ["IR-14"], expected_entity_ids: ["asset:CV-220"], expects_citation: true },
  { id: "q21", question: "What is HX-08's tube bundle cleaning record status?", expected_document_ids: ["ASSET-REGISTRY"], expected_entity_ids: ["asset:HX-08"], expects_citation: true },
];

export const MOCK_EVAL_RESULT: EvalRunResult = {
  retrieval_hit_rate: 0.86,
  citation_coverage: 0.93,
  avg_latency_ms: 412,
  entity_linkage_coverage: 0.79,
  results: MOCK_BENCHMARK_QUESTIONS.map((q, i) => ({
    question_id: q.id,
    passed: i % 6 !== 5,
    latency_ms: 320 + ((i * 37) % 260),
  })),
};

// ---------------------------------------------------------------------------
// Graph (knowledge graph explorer)
// ---------------------------------------------------------------------------

const PEOPLE = [
  { id: "person:j_alvarez", label: "J. Alvarez — Shift Lead" },
  { id: "person:p_singh", label: "P. Singh — Reliability Engineer" },
  { id: "person:m_chen", label: "M. Chen — Compliance Auditor" },
  { id: "person:r_osei", label: "R. Osei — Boiler Operator" },
  { id: "person:t_rivera", label: "T. Rivera — Maintenance Planner" },
];

const FAILURE_MODES = [
  { id: "failure_mode:mechanical_seal_leak", label: "Mechanical seal leakage" },
  { id: "failure_mode:bearing_overheat", label: "Bearing overheating" },
  { id: "failure_mode:relief_valve_drift", label: "Relief valve set-point drift" },
  { id: "failure_mode:belt_slip", label: "Belt slip / tracking drift" },
  { id: "failure_mode:insulation_degradation", label: "Insulation degradation" },
  { id: "failure_mode:valve_wear", label: "Suction valve wear" },
];

const PROCEDURES = [
  { id: "procedure:PROC-LOTO-01", label: "PROC-LOTO-01 — Lockout-Tagout" },
  { id: "procedure:PROC-CONFINED-SPACE", label: "PROC-CONFINED-SPACE — Entry Permit" },
  { id: "procedure:PROC-VIBRATION-MONITORING", label: "PROC-VIBRATION-MONITORING" },
  { id: "procedure:PROC-RELIEF-VALVE-TEST", label: "PROC-RELIEF-VALVE-TEST" },
  { id: "procedure:PROC-BELT-INSPECTION", label: "PROC-BELT-INSPECTION" },
];

const REGULATIONS = [
  { id: "reg:OSHA-301", label: "OSHA 301 — Pressure Vessel Checklist" },
  { id: "reg:REG-089", label: "REG-089 — Relief Valve Testing" },
  { id: "reg:REG-045", label: "REG-045 — LOTO Standard" },
  { id: "reg:REG-112", label: "REG-112 — Insulation Test Standard" },
  { id: "reg:OSHA-146", label: "OSHA 146 — Confined Space Entry" },
  { id: "reg:REG-077", label: "REG-077 — Machine Guarding" },
];

const EXTRA_INCIDENTS = [
  { id: "incident:IR-19", label: "IR-19 — P-104 Seal Failure" },
  { id: "incident:IR-03", label: "IR-03 — B-12 Low-Water Cutoff Failure" },
  { id: "incident:IR-22", label: "IR-22 — CP-303 Valve Wear Trip" },
];

function assetNodeId(tag: string) {
  return `asset:${tag}`;
}
function docNodeId(id: string) {
  return `doc:${id}`;
}

const CORE_NODES: GraphNode[] = [
  ...MOCK_ASSETS.map((a) => ({ id: assetNodeId(a.tag), type: "asset", label: `${a.tag} — ${a.name}` })),
  ...MOCK_DOCUMENTS.map((d) => ({ id: docNodeId(d.id), type: d.doc_type, label: d.title })),
  ...PEOPLE.map((p) => ({ id: p.id, type: "person", label: p.label })),
  ...FAILURE_MODES.map((f) => ({ id: f.id, type: "failure_mode", label: f.label })),
  ...PROCEDURES.map((p) => ({ id: p.id, type: "procedure", label: p.label })),
  ...REGULATIONS.map((r) => ({ id: r.id, type: "regulation", label: r.label })),
  ...EXTRA_INCIDENTS.map((i) => ({ id: i.id, type: "incident", label: i.label })),
];

const CORE_EDGES: GraphEdge[] = [
  // P-101 web
  { source: assetNodeId("P-101"), target: docNodeId("SOP-CENT-PUMP-01"), relationship_type: "asset->document" },
  { source: assetNodeId("P-101"), target: docNodeId("OEM-P101-MANUAL"), relationship_type: "asset->document" },
  { source: assetNodeId("P-101"), target: docNodeId("WO-1042"), relationship_type: "asset->work_order" },
  { source: assetNodeId("P-101"), target: docNodeId("WO-1058"), relationship_type: "asset->work_order" },
  { source: assetNodeId("P-101"), target: docNodeId("WO-1071"), relationship_type: "asset->work_order" },
  { source: assetNodeId("P-101"), target: docNodeId("IR-07"), relationship_type: "asset->incident" },
  { source: assetNodeId("P-101"), target: docNodeId("IR-11"), relationship_type: "asset->incident" },
  { source: assetNodeId("P-101"), target: docNodeId("SHIFT-HANDOVER-0619"), relationship_type: "asset->document" },
  { source: assetNodeId("P-101"), target: "procedure:PROC-LOTO-01", relationship_type: "asset->procedure" },
  { source: assetNodeId("P-101"), target: "procedure:PROC-VIBRATION-MONITORING", relationship_type: "asset->procedure" },
  { source: docNodeId("WO-1042"), target: "failure_mode:mechanical_seal_leak", relationship_type: "work_order->failure_mode" },
  { source: docNodeId("WO-1071"), target: "failure_mode:mechanical_seal_leak", relationship_type: "work_order->failure_mode" },
  { source: docNodeId("WO-1058"), target: "failure_mode:bearing_overheat", relationship_type: "work_order->failure_mode" },
  { source: docNodeId("IR-07"), target: "failure_mode:mechanical_seal_leak", relationship_type: "work_order->failure_mode" },
  { source: docNodeId("IR-11"), target: "failure_mode:bearing_overheat", relationship_type: "work_order->failure_mode" },
  { source: docNodeId("IR-07"), target: docNodeId("IR-11"), relationship_type: "incident->incident" },
  { source: docNodeId("IR-07"), target: "incident:IR-19", relationship_type: "incident->incident" },
  { source: docNodeId("IR-07"), target: "reg:REG-045", relationship_type: "incident->regulation" },
  { source: "person:p_singh", target: docNodeId("WO-1042"), relationship_type: "asset->document" },
  { source: "person:j_alvarez", target: docNodeId("SHIFT-HANDOVER-0619"), relationship_type: "asset->document" },

  // B-12 web
  { source: assetNodeId("B-12"), target: docNodeId("SOP-BOILER-12"), relationship_type: "asset->document" },
  { source: assetNodeId("B-12"), target: docNodeId("INSPECTION-B12-Q2"), relationship_type: "asset->document" },
  { source: assetNodeId("B-12"), target: docNodeId("ASSET-REGISTRY"), relationship_type: "asset->document" },
  { source: assetNodeId("B-12"), target: "procedure:PROC-RELIEF-VALVE-TEST", relationship_type: "asset->procedure" },
  { source: docNodeId("INSPECTION-B12-Q2"), target: "reg:REG-089", relationship_type: "incident->regulation" },
  { source: docNodeId("INSPECTION-B12-Q2"), target: "reg:OSHA-301", relationship_type: "incident->regulation" },
  { source: docNodeId("INSPECTION-B12-Q2"), target: "failure_mode:relief_valve_drift", relationship_type: "inspection->compliance_gap" },
  { source: assetNodeId("B-12"), target: "incident:IR-03", relationship_type: "asset->incident" },
  { source: "person:r_osei", target: docNodeId("SOP-BOILER-12"), relationship_type: "asset->document" },
  { source: "person:m_chen", target: docNodeId("INSPECTION-B12-Q2"), relationship_type: "asset->document" },

  // CP-303
  { source: assetNodeId("CP-303"), target: "incident:IR-22", relationship_type: "asset->incident" },
  { source: assetNodeId("CP-303"), target: "procedure:PROC-CONFINED-SPACE", relationship_type: "asset->procedure" },
  { source: assetNodeId("CP-303"), target: "reg:OSHA-146", relationship_type: "asset->document" },
  { source: "incident:IR-22", target: "failure_mode:valve_wear", relationship_type: "work_order->failure_mode" },

  // TX-450
  { source: assetNodeId("TX-450"), target: docNodeId("INSPECTION-TX450"), relationship_type: "asset->document" },
  { source: docNodeId("INSPECTION-TX450"), target: "reg:REG-112", relationship_type: "incident->regulation" },
  { source: docNodeId("INSPECTION-TX450"), target: "failure_mode:insulation_degradation", relationship_type: "inspection->compliance_gap" },
  { source: "person:t_rivera", target: docNodeId("INSPECTION-TX450"), relationship_type: "asset->document" },

  // CV-220
  { source: assetNodeId("CV-220"), target: docNodeId("WO-2004"), relationship_type: "asset->work_order" },
  { source: assetNodeId("CV-220"), target: docNodeId("IR-14"), relationship_type: "asset->incident" },
  { source: assetNodeId("CV-220"), target: "procedure:PROC-BELT-INSPECTION", relationship_type: "asset->procedure" },
  { source: docNodeId("IR-14"), target: "failure_mode:belt_slip", relationship_type: "work_order->failure_mode" },
  { source: docNodeId("IR-14"), target: "reg:REG-077", relationship_type: "incident->regulation" },

  // HX-08
  { source: assetNodeId("HX-08"), target: docNodeId("ASSET-REGISTRY"), relationship_type: "asset->document" },
];

/** Deterministic filler network so the Graph Explorer can demonstrate hundreds-of-nodes
 *  performance, per ADR-006 / MASTER_SPEC §5 ("must be performant for demo-sized graphs"). */
function buildFillerGraph(): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const assetTags = MOCK_ASSETS.map((a) => a.tag);
  const FILLER_COUNT = 160;
  for (let i = 0; i < FILLER_COUNT; i++) {
    const tag = assetTags[i % assetTags.length];
    const kind = i % 3;
    const id = `filler:WO-${4000 + i}`;
    if (kind === 0) {
      nodes.push({ id, type: "work_order", label: `WO-${4000 + i} Routine PM — ${tag}` });
    } else if (kind === 1) {
      nodes.push({ id, type: "inspection", label: `INSP-${4000 + i} Scheduled Check — ${tag}` });
    } else {
      nodes.push({ id, type: "document", label: `Shift Note ${4000 + i} — ${tag}` });
    }
    edges.push({ source: assetNodeId(tag), target: id, relationship_type: "asset->document" });
    // occasional cross-link to a failure mode for graph texture
    if (i % 5 === 0) {
      edges.push({ source: id, target: FAILURE_MODES[i % FAILURE_MODES.length].id, relationship_type: "work_order->failure_mode" });
    }
  }
  return { nodes, edges };
}

const FILLER = buildFillerGraph();

export const MOCK_GRAPH_ALL: GraphNeighborhood = {
  nodes: [...CORE_NODES, ...FILLER.nodes],
  edges: [...CORE_EDGES, ...FILLER.edges],
};

/** BFS neighborhood extraction from the master mock graph, mirroring the real
 *  `GET /graph/neighborhood?node_id=&depth=` contract shape exactly. */
export function getMockGraphNeighborhood(nodeId?: string, depth = 1): GraphNeighborhood {
  if (!nodeId) {
    return MOCK_GRAPH_ALL;
  }
  const adjacency = new Map<string, { neighbor: string; edge: GraphEdge }[]>();
  for (const e of MOCK_GRAPH_ALL.edges) {
    if (!adjacency.has(e.source)) adjacency.set(e.source, []);
    if (!adjacency.has(e.target)) adjacency.set(e.target, []);
    adjacency.get(e.source)!.push({ neighbor: e.target, edge: e });
    adjacency.get(e.target)!.push({ neighbor: e.source, edge: e });
  }
  const visited = new Set<string>([nodeId]);
  const frontier = [nodeId];
  const edgeSet = new Set<GraphEdge>();
  for (let d = 0; d < depth; d++) {
    const next: string[] = [];
    for (const nid of frontier) {
      for (const { neighbor, edge } of adjacency.get(nid) ?? []) {
        edgeSet.add(edge);
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          next.push(neighbor);
        }
      }
    }
    frontier.length = 0;
    frontier.push(...next);
  }
  const nodeById = new Map(MOCK_GRAPH_ALL.nodes.map((n) => [n.id, n]));
  const nodes = Array.from(visited)
    .map((id) => nodeById.get(id))
    .filter((n): n is GraphNode => Boolean(n));
  return { nodes, edges: Array.from(edgeSet) };
}

export function assetIdToGraphNodeId(assetIdOrTag: string): string {
  return assetNodeId(assetIdOrTag);
}

// ---------------------------------------------------------------------------
// Dashboard-only derived types (no dedicated backend endpoint per MASTER_SPEC §6;
// composed client-side from /assets, /assets/{id}/three_sixty, and /compliance/gaps)
// ---------------------------------------------------------------------------

export interface DashboardAlert {
  id: string;
  severity: "low" | "medium" | "high";
  title: string;
  detail: string;
  assetTag?: string;
}

export interface RepeatedIssue {
  failure_mode: string;
  count: number;
  assets_affected: string[];
}

export const MOCK_REPEATED_ISSUES: RepeatedIssue[] = [
  { failure_mode: "Mechanical seal leakage", count: 4, assets_affected: ["P-101"] },
  { failure_mode: "Relief valve set-point drift", count: 3, assets_affected: ["B-12"] },
  { failure_mode: "Bearing overheating", count: 2, assets_affected: ["P-101"] },
];

export function getMockDashboardAlerts(): DashboardAlert[] {
  return [
    { id: "alert-1", severity: "high", title: "B-12 missing relief valve test certificate", detail: "No certified test on file since 2024-11 — REG-089 non-compliance risk.", assetTag: "B-12" },
    { id: "alert-2", severity: "high", title: "P-101 seal failure recurrence", detail: "4th mechanical seal failure in 14 months; low-flow operation root cause confirmed.", assetTag: "P-101" },
    { id: "alert-3", severity: "medium", title: "CP-303 confined space permit missing", detail: "No permit on file for last compressor overhaul.", assetTag: "CP-303" },
    { id: "alert-4", severity: "low", title: "CV-220 guarding inspection overdue", detail: "Inspection overdue by 12 days following a belt-slip near-miss.", assetTag: "CV-220" },
  ];
}
