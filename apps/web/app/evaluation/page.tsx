"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { StatTile } from "@/components/cards/StatTile";
import { AsyncSection, EmptyBlock } from "@/components/States";
import { getEvalQuestions, postEvalRun } from "@/lib/api";
import { formatMs, formatPercent } from "@/lib/utils";
import type { BenchmarkQuestion, EvalRunResult } from "@shared/types";

export default function EvaluationPage() {
  const [questions, setQuestions] = useState<BenchmarkQuestion[] | null>(null);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [questionsError, setQuestionsError] = useState<string | null>(null);

  const [result, setResult] = useState<EvalRunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [source, setSource] = useState<"live" | "mock" | null>(null);

  useEffect(() => {
    let cancelled = false;
    getEvalQuestions()
      .then((res) => {
        if (!cancelled) setQuestions(res.data);
      })
      .catch((err) => {
        if (!cancelled) setQuestionsError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoadingQuestions(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function runBenchmark() {
    setRunning(true);
    setRunError(null);
    try {
      const res = await postEvalRun();
      setResult(res.data);
      setSource(res.source);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  const resultByQuestionId = new Map((result?.results ?? []).map((r) => [r.question_id, r]));

  return (
    <div>
      <PageHeader
        title="Evaluation / Benchmark"
        description="Quality metrics that prove OpsBrain's answers are grounded, not a fake UI — retrieval hit rate, citation coverage, latency, and entity linkage coverage."
        action={
          <button
            onClick={runBenchmark}
            disabled={running}
            className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-semibold text-brand-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? "Running benchmark…" : "Run Benchmark"}
          </button>
        }
      />

      {source === "mock" && (
        <p className="mb-4 text-xs text-brand-warn">Demo Mode — showing seeded mock benchmark results (backend unreachable).</p>
      )}

      {runError && <p className="mb-4 text-sm text-brand-danger">{runError}</p>}

      {result ? (
        <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatTile label="Retrieval Hit Rate" value={formatPercent(result.retrieval_hit_rate)} tone="accent" />
          <StatTile label="Citation Coverage" value={formatPercent(result.citation_coverage)} tone="accent" />
          <StatTile label="Avg Latency" value={formatMs(result.avg_latency_ms)} />
          <StatTile label="Entity Linkage Coverage" value={formatPercent(result.entity_linkage_coverage)} />
        </div>
      ) : (
        <div className="mb-8">
          <EmptyBlock label='No benchmark run yet — click "Run Benchmark" to score OpsBrain against the question set below.' />
        </div>
      )}

      <SectionCard
        title="Benchmark Questions"
        subtitle={questions ? `${questions.length} questions, each expecting ≥1 citation` : undefined}
      >
        <AsyncSection
          loading={loadingQuestions}
          error={questionsError}
          data={questions}
          isEmpty={(d) => !d || d.length === 0}
          loadingLabel="Loading benchmark question set…"
          emptyLabel="No benchmark questions found."
        >
          {(data) => (
            <ul className="divide-y divide-brand-border">
              {(data as BenchmarkQuestion[]).map((q) => {
                const r = resultByQuestionId.get(q.id);
                return (
                  <li key={q.id} className="flex items-start justify-between gap-4 py-3 first:pt-0 last:pb-0">
                    <div>
                      <p className="text-sm text-slate-100">{q.question}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Expects {q.expected_document_ids.length} doc(s), {q.expected_entity_ids.length} entit
                        {q.expected_entity_ids.length === 1 ? "y" : "ies"}
                        {q.expects_citation ? ", citation required" : ""}
                      </p>
                    </div>
                    {r && (
                      <div className="shrink-0 text-right">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                            r.passed ? "bg-brand-accent/15 text-brand-accent" : "bg-brand-danger/15 text-brand-danger"
                          }`}
                        >
                          {r.passed ? "Passed" : "Failed"}
                        </span>
                        <p className="mt-1 text-xs text-slate-500">{formatMs(r.latency_ms)}</p>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </AsyncSection>
      </SectionCard>
    </div>
  );
}
