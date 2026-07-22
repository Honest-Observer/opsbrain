"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { StatTile } from "@/components/cards/StatTile";
import { SeverityBadge } from "@/components/badges/SeverityBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { AsyncSection, EmptyBlock } from "@/components/States";
import { getComplianceGaps } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import type { ComplianceGap, Severity, ComplianceStatus } from "@shared/types";

const STATUS_OPTIONS: (ComplianceStatus | "all")[] = ["all", "gap", "at_risk", "ok"];
const SEVERITY_OPTIONS: (Severity | "all")[] = ["all", "high", "medium", "low"];

export default function ComplianceBoardPage() {
  const [gaps, setGaps] = useState<ComplianceGap[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"live" | "mock" | null>(null);
  const [statusFilter, setStatusFilter] = useState<ComplianceStatus | "all">("all");
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getComplianceGaps()
      .then((res) => {
        if (cancelled) return;
        setGaps(res.data);
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
  }, []);

  const filtered = useMemo(() => {
    if (!gaps) return [];
    return gaps.filter(
      (g) => (statusFilter === "all" || g.status === statusFilter) && (severityFilter === "all" || g.severity === severityFilter)
    );
  }, [gaps, statusFilter, severityFilter]);

  const summary = useMemo(() => {
    if (!gaps) return { total: 0, gap: 0, atRisk: 0, ok: 0, coverage: 0 };
    const gap = gaps.filter((g) => g.status === "gap").length;
    const atRisk = gaps.filter((g) => g.status === "at_risk").length;
    const ok = gaps.filter((g) => g.status === "ok").length;
    return { total: gaps.length, gap, atRisk, ok, coverage: gaps.length ? ok / gaps.length : 0 };
  }, [gaps]);

  return (
    <div>
      <PageHeader
        title="Compliance Board"
        description="Evidence coverage against the demo regulatory / SOP checklist, with gap severity and corrective action suggestions."
      />

      <AsyncSection
        loading={loading}
        error={error}
        data={gaps}
        isEmpty={(d) => !d || d.length === 0}
        loadingLabel="Loading compliance gaps…"
        emptyLabel="No compliance checklist items found."
      >
        {() => (
          <div className="space-y-6">
            {source === "mock" && (
              <p className="text-xs text-brand-warn">Demo Mode — showing seeded mock data (backend unreachable).</p>
            )}

            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <StatTile label="Checklist Items" value={summary.total} />
              <StatTile label="Open Gaps" value={summary.gap} tone="danger" />
              <StatTile label="At Risk" value={summary.atRisk} tone="warn" />
              <StatTile label="Evidence Coverage" value={formatPercent(summary.coverage)} tone="accent" sub={`${summary.ok} of ${summary.total} items OK`} />
            </div>

            <SectionCard
              title="Checklist Items"
              subtitle="Filter by status / severity to prioritize corrective action"
              action={
                <div className="flex gap-2">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as ComplianceStatus | "all")}
                    className="rounded-lg border border-brand-border bg-brand-bg px-2 py-1 text-xs text-slate-200 focus:border-brand-accent focus:outline-none"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s === "all" ? "All statuses" : s}
                      </option>
                    ))}
                  </select>
                  <select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value as Severity | "all")}
                    className="rounded-lg border border-brand-border bg-brand-bg px-2 py-1 text-xs text-slate-200 focus:border-brand-accent focus:outline-none"
                  >
                    {SEVERITY_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s === "all" ? "All severities" : s}
                      </option>
                    ))}
                  </select>
                </div>
              }
            >
              {filtered.length === 0 ? (
                <EmptyBlock label="No checklist items match the current filters." />
              ) : (
                <ul className="divide-y divide-brand-border">
                  {filtered.map((g) => (
                    <li key={g.id} className="flex flex-col gap-2 py-4 first:pt-0 last:pb-0">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <Link href={`/assets/${g.asset_tag}`} className="text-sm font-semibold text-brand-accent hover:underline">
                            {g.asset_tag}
                          </Link>
                          <p className="text-sm text-slate-100">{g.checklist_item}</p>
                          {g.regulation_ref && <p className="text-xs text-slate-500">Ref: {g.regulation_ref}</p>}
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <SeverityBadge severity={g.severity} />
                          <StatusBadge status={g.status} />
                        </div>
                      </div>
                      {(g.missing_evidence || g.corrective_action) && (
                        <div className="rounded-lg border border-brand-border bg-brand-bg/60 p-3 text-xs">
                          {g.missing_evidence && (
                            <p className="text-slate-400">
                              <span className="font-semibold text-slate-300">Missing evidence: </span>
                              {g.missing_evidence}
                            </p>
                          )}
                          {g.corrective_action && (
                            <p className="mt-1 text-brand-accent">
                              <span className="font-semibold">Corrective action: </span>
                              {g.corrective_action}
                            </p>
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          </div>
        )}
      </AsyncSection>
    </div>
  );
}
