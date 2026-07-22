"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { CriticalityBadge } from "@/components/badges/CriticalityBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { SeverityBadge } from "@/components/badges/SeverityBadge";
import { PriorityBadge } from "@/components/badges/PriorityBadge";
import { AsyncSection, EmptyBlock } from "@/components/States";
import { getAssetThreeSixty } from "@/lib/api";
import { formatDate, formatPercent, titleCase } from "@/lib/utils";
import type { AssetThreeSixty } from "@shared/types";

export default function AssetThreeSixtyPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [data, setData] = useState<AssetThreeSixty | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"live" | "mock" | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getAssetThreeSixty(id)
      .then((res) => {
        if (cancelled) return;
        setData(res.data);
        setSource(res.source);
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
  }, [id]);

  return (
    <div>
      <PageHeader
        title={`Asset 360 — ${id}`}
        description="Maintenance history, recurring issues, similar incidents, compliance gaps, and recommended actions for this asset, in one view."
      />

      <AsyncSection
        loading={loading}
        error={error}
        data={data}
        isEmpty={(d) => d === null}
        loadingLabel="Loading asset 360…"
        emptyLabel={`No data found for asset "${id}".`}
      >
        {(d) => {
          const a360 = d as AssetThreeSixty;
          return (
            <div className="space-y-6">
              {source === "mock" && (
                <p className="text-xs text-brand-warn">Demo Mode — showing seeded mock data (backend unreachable).</p>
              )}

              <SectionCard title="Asset Summary">
                <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
                  <div>
                    <p className="text-lg font-semibold text-slate-50">
                      {a360.asset.tag} — {a360.asset.name}
                    </p>
                    <p className="text-sm text-slate-400">
                      {a360.asset.asset_type} · {a360.asset.location}
                    </p>
                  </div>
                  <CriticalityBadge criticality={a360.asset.criticality} />
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Risk Score</span>
                    <span className="text-lg font-semibold tabular-nums text-brand-danger">{a360.asset.risk_score}</span>
                  </div>
                  {typeof a360.asset.open_issues === "number" && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">Open Issues</span>
                      <span className="text-lg font-semibold tabular-nums text-slate-200">{a360.asset.open_issues}</span>
                    </div>
                  )}
                </div>
              </SectionCard>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SectionCard title="Recurring Failure Patterns">
                  {a360.recurring_issues.length === 0 ? (
                    <EmptyBlock label="No recurring failure patterns detected for this asset." />
                  ) : (
                    <ul className="space-y-3">
                      {a360.recurring_issues.map((r) => (
                        <li key={r.failure_mode} className="flex items-center justify-between text-sm">
                          <div>
                            <p className="font-medium text-slate-100">{r.failure_mode}</p>
                            <p className="text-xs text-slate-500">Last seen {formatDate(r.last_seen)}</p>
                          </div>
                          <span className="rounded-full bg-brand-border px-2 py-0.5 text-xs font-semibold text-slate-200">
                            ×{r.count}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>

                <SectionCard title="Similar Incidents">
                  {a360.similar_incidents.length === 0 ? (
                    <EmptyBlock label="No similar past incidents found." />
                  ) : (
                    <ul className="space-y-3">
                      {a360.similar_incidents.map((s) => (
                        <li key={s.incident_id} className="rounded-lg border border-brand-border bg-brand-bg/60 p-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-medium text-slate-100">
                              {s.incident_id} — {s.title}
                            </p>
                            <span className="shrink-0 text-xs font-semibold text-brand-accent">
                              {formatPercent(s.similarity)} match
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-slate-400">{s.summary}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>
              </div>

              <SectionCard title="Maintenance Timeline">
                {a360.timeline.length === 0 ? (
                  <EmptyBlock label="No timeline events recorded." />
                ) : (
                  <ol className="relative space-y-5 border-l border-brand-border pl-5">
                    {a360.timeline.map((t, i) => (
                      <li key={i} className="relative">
                        <span className="absolute -left-[25px] top-1 h-2.5 w-2.5 rounded-full border-2 border-brand-bg bg-brand-accent" />
                        <div className="flex flex-wrap items-baseline gap-2">
                          <span className="text-xs font-semibold text-slate-500">{formatDate(t.date)}</span>
                          <span className="rounded bg-brand-border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
                            {titleCase(t.type)}
                          </span>
                          <span className="text-sm font-medium text-slate-100">{t.title}</span>
                          <span className="text-xs text-slate-500">({t.ref_id})</span>
                        </div>
                        <p className="mt-1 text-xs text-slate-400">{t.summary}</p>
                      </li>
                    ))}
                  </ol>
                )}
              </SectionCard>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SectionCard title="Compliance Issues">
                  {a360.compliance_issues.length === 0 ? (
                    <EmptyBlock label="No compliance issues tracked for this asset." />
                  ) : (
                    <ul className="space-y-3">
                      {a360.compliance_issues.map((c, i) => (
                        <li key={i} className="flex items-center justify-between gap-3 text-sm">
                          <span className="text-slate-100">{c.checklist_item}</span>
                          <div className="flex shrink-0 items-center gap-2">
                            <SeverityBadge severity={c.severity} />
                            <StatusBadge status={c.status} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>

                <SectionCard title="Linked Documents">
                  {a360.linked_documents.length === 0 ? (
                    <EmptyBlock label="No documents linked yet." />
                  ) : (
                    <ul className="space-y-2">
                      {a360.linked_documents.map((doc) => (
                        <li key={doc.id} className="flex items-center justify-between gap-3 text-sm">
                          <span className="text-slate-200">{doc.title}</span>
                          <span className="shrink-0 rounded bg-brand-border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
                            {doc.doc_type}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </SectionCard>
              </div>

              <SectionCard title="Recommended Actions">
                {a360.recommended_actions.length === 0 ? (
                  <EmptyBlock label="No recommended actions at this time." />
                ) : (
                  <ul className="space-y-3">
                    {a360.recommended_actions.map((a, i) => (
                      <li key={i} className="rounded-lg border border-brand-border bg-brand-bg/60 p-3">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-medium text-slate-100">{a.action}</p>
                          <PriorityBadge priority={a.priority} className="shrink-0" />
                        </div>
                        <p className="mt-1 text-xs text-slate-400">{a.rationale}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>

              <p className="text-xs text-slate-600">
                Looking for a different asset?{" "}
                <Link href="/dashboard" className="text-brand-accent hover:underline">
                  Back to Dashboard
                </Link>
              </p>
            </div>
          );
        }}
      </AsyncSection>
    </div>
  );
}
