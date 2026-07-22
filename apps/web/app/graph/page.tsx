"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { LoadingBlock, EmptyBlock } from "@/components/States";
import { getAssets, getGraphNeighborhood } from "@/lib/api";
import { computeLayout, colorForType } from "@/lib/graphLayout";
import type { Asset, GraphNeighborhood, GraphNode as OpsGraphNode } from "@shared/types";

function toAssetNodeId(tag: string) {
  return `asset:${tag}`;
}

export default function GraphExplorerPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [depth, setDepth] = useState(2);
  const [anchorNodeId, setAnchorNodeId] = useState<string | null>(null);
  const [manualNodeId, setManualNodeId] = useState("");
  const [graph, setGraph] = useState<GraphNeighborhood | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"live" | "mock" | null>(null);
  const [selected, setSelected] = useState<OpsGraphNode | null>(null);
  const [fullView, setFullView] = useState(false);

  useEffect(() => {
    getAssets().then((res) => {
      setAssets(res.data);
      if (res.data.length > 0) setAnchorNodeId(toAssetNodeId(res.data[0].tag));
    });
  }, []);

  useEffect(() => {
    if (!anchorNodeId && !fullView) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    getGraphNeighborhood(fullView ? undefined : anchorNodeId ?? undefined, depth)
      .then((res) => {
        if (cancelled) return;
        setGraph(res.data);
        setSource(res.source);
        setSelected(null);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [anchorNodeId, depth, fullView]);

  const laidOut = useMemo(() => computeLayout(graph?.nodes ?? []), [graph]);

  const rfNodes: Node[] = useMemo(
    () =>
      laidOut.map((n) => ({
        id: n.id,
        position: { x: n.x, y: n.y },
        data: { label: n.label },
        style: {
          background: "#121821",
          border: `1.5px solid ${colorForType(n.type)}`,
          color: "#e2e8f0",
          borderRadius: 8,
          fontSize: 11,
          padding: "6px 10px",
          width: 180,
        },
      })),
    [laidOut]
  );

  const rfEdges: Edge[] = useMemo(
    () =>
      (graph?.edges ?? []).map((e, i) => ({
        id: `${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        label: e.relationship_type,
        style: { stroke: "#232c38" },
        labelStyle: { fill: "#64748b", fontSize: 9 },
        animated: false,
      })),
    [graph]
  );

  const relatedEdges = useMemo(() => {
    if (!selected || !graph) return [];
    return graph.edges.filter((e) => e.source === selected.id || e.target === selected.id);
  }, [selected, graph]);

  const nodeById = useMemo(() => new Map((graph?.nodes ?? []).map((n) => [n.id, n])), [graph]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      const found = nodeById.get(node.id);
      if (found) setSelected(found);
    },
    [nodeById]
  );

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <PageHeader
        title="Knowledge Graph Explorer"
        description="Interactive view of the asset / document / incident / regulation graph. Click any node to inspect its relationships."
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-slate-400">
          Anchor asset
          <select
            value={fullView ? "" : anchorNodeId ?? ""}
            onChange={(e) => {
              setFullView(false);
              setAnchorNodeId(e.target.value);
            }}
            className="rounded-lg border border-brand-border bg-brand-bg px-2 py-1.5 text-sm text-slate-100 focus:border-brand-accent focus:outline-none"
          >
            {assets.map((a) => (
              <option key={a.id} value={toAssetNodeId(a.tag)}>
                {a.tag} — {a.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-xs text-slate-400">
          Depth
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            className="rounded-lg border border-brand-border bg-brand-bg px-2 py-1.5 text-sm text-slate-100 focus:border-brand-accent focus:outline-none"
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </label>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (manualNodeId.trim()) {
              setFullView(false);
              setAnchorNodeId(manualNodeId.trim());
            }
          }}
          className="flex items-center gap-2"
        >
          <input
            value={manualNodeId}
            onChange={(e) => setManualNodeId(e.target.value)}
            placeholder="Jump to node id (e.g. doc:IR-07)"
            className="w-56 rounded-lg border border-brand-border bg-brand-bg px-3 py-1.5 text-xs text-slate-100 placeholder:text-slate-500 focus:border-brand-accent focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-lg border border-brand-border px-3 py-1.5 text-xs text-slate-300 hover:border-brand-accent hover:text-brand-accent"
          >
            Go
          </button>
        </form>

        <button
          onClick={() => setFullView((v) => !v)}
          className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
            fullView
              ? "border-brand-accent text-brand-accent"
              : "border-brand-border text-slate-300 hover:border-brand-accent hover:text-brand-accent"
          }`}
        >
          {fullView ? "Showing full plant graph" : "Show full plant graph"}
        </button>

        {source === "mock" && (
          <span className="text-xs text-brand-warn">Demo Mode — seeded mock graph (backend unreachable)</span>
        )}
        {graph && (
          <span className="text-xs text-slate-500">
            {graph.nodes.length} nodes · {graph.edges.length} edges
          </span>
        )}
      </div>

      <div className="flex flex-1 gap-4 overflow-hidden">
        <SectionCard title="" className="flex-1 !p-0 overflow-hidden">
          <div className="h-[60vh] w-full">
            {loading ? (
              <LoadingBlock label="Loading graph…" />
            ) : error ? (
              <p className="p-6 text-sm text-brand-danger">{error}</p>
            ) : !graph || graph.nodes.length === 0 ? (
              <EmptyBlock label="No graph data available." />
            ) : (
              <ReactFlow
                nodes={rfNodes}
                edges={rfEdges}
                onNodeClick={onNodeClick}
                fitView
                minZoom={0.1}
                nodesConnectable={false}
                edgesFocusable={false}
                proOptions={{ hideAttribution: true }}
              >
                <Background color="#232c38" gap={24} />
                <Controls />
                <MiniMap
                  nodeColor={(n) => (n.style?.border as string)?.split(" ").pop() ?? "#64748b"}
                  maskColor="rgba(11,15,20,0.7)"
                  style={{ background: "#121821" }}
                />
              </ReactFlow>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Node Inspector" className="w-80 shrink-0 overflow-y-auto">
          {!selected ? (
            <EmptyBlock label="Click a node in the graph to inspect its details and relationships." />
          ) : (
            <div className="space-y-4">
              <div>
                <span
                  className="mb-1 inline-block rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide"
                  style={{ background: `${colorForType(selected.type)}22`, color: colorForType(selected.type) }}
                >
                  {selected.type}
                </span>
                <p className="text-sm font-semibold text-slate-100">{selected.label}</p>
                <p className="mt-0.5 text-xs text-slate-500">{selected.id}</p>
              </div>

              {selected.type === "asset" && (
                <a
                  href={`/assets/${selected.id.replace(/^asset:/, "")}`}
                  className="inline-block text-xs font-medium text-brand-accent hover:underline"
                >
                  Open Asset 360 →
                </a>
              )}

              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Relationships ({relatedEdges.length})
                </p>
                {relatedEdges.length === 0 ? (
                  <p className="text-xs text-slate-500">No relationships in the current view.</p>
                ) : (
                  <ul className="space-y-2">
                    {relatedEdges.map((e, i) => {
                      const otherId = e.source === selected.id ? e.target : e.source;
                      const other = nodeById.get(otherId);
                      const direction = e.source === selected.id ? "→" : "←";
                      return (
                        <li key={i} className="rounded-lg border border-brand-border bg-brand-bg/60 p-2 text-xs">
                          <span className="text-slate-500">{e.relationship_type}</span>
                          <div className="mt-0.5 flex items-center gap-1 text-slate-200">
                            <span className="text-slate-500">{direction}</span>
                            <button
                              onClick={() => other && setSelected(other)}
                              className="text-left text-brand-accent hover:underline"
                            >
                              {other?.label ?? otherId}
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
