import type { GraphNode } from "@shared/types";

/**
 * Deterministic grid/band layout so the Graph Explorer never needs a heavy
 * external layout dependency (dagre/elkjs) beyond the `reactflow` package
 * already in package.json (ADR-006). Groups nodes by entity type into
 * horizontal bands, wrapping long bands into sub-rows so demo-sized graphs
 * (hundreds of nodes) stay readable and cheap to compute.
 */
const TYPE_ORDER = [
  "asset",
  "document",
  "sop",
  "manual",
  "incident",
  "work_order",
  "inspection",
  "regulation",
  "procedure",
  "failure_mode",
  "person",
  "handover",
  "registry",
];

const COL_WIDTH = 210;
const ROW_HEIGHT = 170;
const SUBROW_HEIGHT = 90;
const MAX_COLS = 10;

export interface LaidOutNode extends GraphNode {
  x: number;
  y: number;
}

export function computeLayout(nodes: GraphNode[]): LaidOutNode[] {
  const byType = new Map<string, GraphNode[]>();
  for (const n of nodes) {
    if (!byType.has(n.type)) byType.set(n.type, []);
    byType.get(n.type)!.push(n);
  }

  const typesPresent = Array.from(byType.keys()).sort((a, b) => {
    const ia = TYPE_ORDER.indexOf(a);
    const ib = TYPE_ORDER.indexOf(b);
    return (ia === -1 ? TYPE_ORDER.length : ia) - (ib === -1 ? TYPE_ORDER.length : ib);
  });

  const out: LaidOutNode[] = [];
  let bandY = 0;
  for (const type of typesPresent) {
    const group = byType.get(type)!;
    const rows = Math.ceil(group.length / MAX_COLS);
    group.forEach((n, i) => {
      const col = i % MAX_COLS;
      const row = Math.floor(i / MAX_COLS);
      out.push({
        ...n,
        x: col * COL_WIDTH,
        y: bandY + row * SUBROW_HEIGHT,
      });
    });
    bandY += Math.max(rows, 1) * SUBROW_HEIGHT + (ROW_HEIGHT - SUBROW_HEIGHT);
  }
  return out;
}

export const TYPE_COLORS: Record<string, string> = {
  asset: "#3ddc97",
  document: "#5aa9e6",
  sop: "#2dd4bf",
  manual: "#2dd4bf",
  incident: "#f5524a",
  work_order: "#94a3b8",
  inspection: "#5aa9e6",
  regulation: "#f5a524",
  procedure: "#a78bfa",
  failure_mode: "#fb7185",
  person: "#818cf8",
  handover: "#94a3b8",
  registry: "#94a3b8",
};

export function colorForType(type: string): string {
  return TYPE_COLORS[type] ?? "#64748b";
}
