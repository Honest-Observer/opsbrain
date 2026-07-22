"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { StatTile } from "@/components/cards/StatTile";
import { SeverityBadge } from "@/components/badges/SeverityBadge";
import { CriticalityBadge } from "@/components/badges/CriticalityBadge";
import { AsyncSection } from "@/components/States";
import { getDashboardData, type DashboardData } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { DEMO_QUERIES } from "@/lib/mockData";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getDashboardData()
      .then((res) => {
        if (!cancelled) setData(res.data);
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
  }, []);

  return (
    <div>
      <PageHeader
        title="OpsBrain — Asset & Operations Brain"
        description="Ask plain-language questions about your plant and get cited, trustworthy, actionable answers. Ingests SOPs, manuals, work orders, incidents, inspections, and regulations into one knowledge graph — and proactively surfaces compliance gaps and past-incident lessons before they repeat."
      />

      <AsyncSection
        loading={loading}
        error={error}
        data={data}
        isEmpty={(d) => d === null}
        loadingLabel="Loading plant overview…"
        emptyLabel="No ingestion data yet — run the demo seed flow from the backend to populate the knowledge graph."
      >
        {(d) => {
          const dash = d as DashboardData;
          return (
            <div className="space-y-8">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <StatTile label="Documents Ingested" value={dash.ingestion.documents} tone="accent" />
                <StatTile label="Chunks Indexed" value={dash.ingestion.chunks} />
                <StatTile label="Entities Extracted" value={dash.ingestion.entities} />
                <StatTile
                  label="Relationships Linked"
                  value={dash.ingestion.relationships}
                  sub={`Last seeded ${formatDateTime(dash.ingestion.last_seeded_at)}`}
                />
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <SectionCard title="Recent Alerts" subtitle="Highest-severity issues across the plant" className="lg:col-span-2">
                  {dash.alerts.length === 0 ? (
                    <p className="text-sm text-slate-500">No active alerts.</p>
                  ) : (
                    <ul className="divide-y divide-brand-border">
                      {dash.alerts.map((alert) => (
                        <li key={alert.id} className="flex items-start justify-between gap-4 py-3 first:pt-0 last:pb-0">
                          <div>
                            <p className="text-sm font-medium text-slate-100">{alert.title}</p>
                            <p className="mt-0.5 text-xs text-slate-400">{alert.detail}</p>
                          </div>
                          <SeverityBadge severity={alert.severity} className="shrink-0" />
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>

                <SectionCard title="Top Repeated Issues" subtitle="Recurring failure modes plant-wide">
                  {dash.repeatedIssues.length === 0 ? (
                    <p className="text-sm text-slate-500">No recurring patterns detected.</p>
                  ) : (
                    <ul className="space-y-3">
                      {dash.repeatedIssues.map((issue) => (
                        <li key={issue.failure_mode} className="flex items-center justify-between text-sm">
                          <div>
                            <p className="font-medium text-slate-100">{issue.failure_mode}</p>
                            <p className="text-xs text-slate-500">{issue.assets_affected.join(", ")}</p>
                          </div>
                          <span className="rounded-full bg-brand-border px-2 py-0.5 text-xs font-semibold text-slate-200">
                            ×{issue.count}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>
              </div>

              <SectionCard title="Top Risky Assets" subtitle="Sorted by composite risk score">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead>
                      <tr className="text-xs uppercase tracking-wide text-slate-500">
                        <th className="pb-2 pr-4 font-medium">Asset</th>
                        <th className="pb-2 pr-4 font-medium">Type</th>
                        <th className="pb-2 pr-4 font-medium">Criticality</th>
                        <th className="pb-2 pr-4 font-medium">Open Issues</th>
                        <th className="pb-2 font-medium">Risk Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-brand-border">
                      {dash.topRiskyAssets.map((asset) => (
                        <tr key={asset.id}>
                          <td className="py-3 pr-4">
                            <Link href={`/assets/${asset.id}`} className="font-medium text-brand-accent hover:underline">
                              {asset.tag}
                            </Link>
                            <p className="text-xs text-slate-500">{asset.name}</p>
                          </td>
                          <td className="py-3 pr-4 text-slate-300">{asset.asset_type}</td>
                          <td className="py-3 pr-4">
                            <CriticalityBadge criticality={asset.criticality} />
                          </td>
                          <td className="py-3 pr-4 text-slate-300">{asset.open_issues ?? 0}</td>
                          <td className="py-3">
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 w-24 overflow-hidden rounded-full bg-brand-border">
                                <div
                                  className="h-full rounded-full bg-brand-danger"
                                  style={{ width: `${Math.min(100, asset.risk_score)}%` }}
                                />
                              </div>
                              <span className="tabular-nums text-slate-200">{asset.risk_score}</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </SectionCard>

              <SectionCard title="Ask OpsBrain" subtitle="Quick demo queries — jump straight into the Copilot">
                <div className="flex flex-wrap gap-2">
                  {DEMO_QUERIES.map((q) => (
                    <Link
                      key={q}
                      href={`/copilot?q=${encodeURIComponent(q)}`}
                      className="rounded-full border border-brand-border bg-brand-bg px-3 py-1.5 text-sm text-slate-200 transition-colors hover:border-brand-accent hover:text-brand-accent"
                    >
                      {q}
                    </Link>
                  ))}
                </div>
              </SectionCard>
            </div>
          );
        }}
      </AsyncSection>
    </div>
  );
}
