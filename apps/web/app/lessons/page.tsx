"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { AsyncSection } from "@/components/States";
import { getAssets, getLessons } from "@/lib/api";
import { formatDate, formatPercent } from "@/lib/utils";
import type { Asset, Lesson } from "@shared/types";

export default function LessonsLearnedPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [assetFilter, setAssetFilter] = useState<string>("");
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"live" | "mock" | null>(null);

  useEffect(() => {
    getAssets().then((res) => setAssets(res.data));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getLessons(assetFilter || undefined)
      .then((res) => {
        if (cancelled) return;
        setLessons(res.data);
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
  }, [assetFilter]);

  return (
    <div>
      <PageHeader
        title="Lessons Learned / Prevention Feed"
        description="Similar past incidents and proactive warnings, surfaced before problems repeat — a push feed, not a search box."
        action={
          <select
            value={assetFilter}
            onChange={(e) => setAssetFilter(e.target.value)}
            className="rounded-lg border border-brand-border bg-brand-bg px-3 py-1.5 text-sm text-slate-200 focus:border-brand-accent focus:outline-none"
          >
            <option value="">All assets</option>
            {assets.map((a) => (
              <option key={a.id} value={a.id}>
                {a.tag} — {a.name}
              </option>
            ))}
          </select>
        }
      />

      {source === "mock" && (
        <p className="mb-4 text-xs text-brand-warn">Demo Mode — showing seeded mock data (backend unreachable).</p>
      )}

      <AsyncSection
        loading={loading}
        error={error}
        data={lessons}
        isEmpty={(d) => !d || d.length === 0}
        loadingLabel="Scanning past incidents for relevant lessons…"
        emptyLabel="No similar past incidents found for this filter."
      >
        {(data) => (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {(data as Lesson[]).map((lesson) => (
              <SectionCard
                key={lesson.incident_id}
                title={`${lesson.incident_id} — ${lesson.title}`}
                subtitle={formatDate(lesson.date)}
                action={
                  <span className="rounded-full bg-brand-accent/15 px-2 py-0.5 text-xs font-semibold text-brand-accent">
                    {formatPercent(lesson.similarity)} similar
                  </span>
                }
              >
                <p className="text-sm text-slate-300">{lesson.summary}</p>
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-brand-warn/40 bg-brand-warn/10 p-3">
                  <span className="mt-0.5 text-brand-warn">⚠</span>
                  <p className="text-xs text-brand-warn">{lesson.warning}</p>
                </div>
              </SectionCard>
            ))}
          </div>
        )}
      </AsyncSection>
    </div>
  );
}
