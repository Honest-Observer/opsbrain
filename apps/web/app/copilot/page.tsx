"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { CitationChip } from "@/components/CitationChip";
import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { PriorityBadge } from "@/components/badges/PriorityBadge";
import { LoadingBlock, EmptyBlock } from "@/components/States";
import { postCopilotAsk } from "@/lib/api";
import { DEMO_QUERIES } from "@/lib/mockData";
import type { CopilotAnswer } from "@shared/types";

function CopilotBody() {
  const searchParams = useSearchParams();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<CopilotAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWhy, setShowWhy] = useState(false);
  const [source, setSource] = useState<"live" | "mock" | null>(null);

  async function ask(q: string) {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setShowWhy(false);
    try {
      const res = await postCopilotAsk(q);
      setAnswer(res.data);
      setSource(res.source);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const q = searchParams?.get("q");
    if (q) {
      setQuestion(q);
      ask(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <PageHeader
        title="Copilot"
        description="Ask a plain-language question about any asset, incident, or compliance item. Every answer is grounded in cited evidence from the plant knowledge graph."
      />

      <SectionCard title="Ask a question" className="mb-6">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(question);
          }}
          className="flex flex-col gap-3"
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder='e.g. "Why is Pump P-101 repeatedly failing?"'
            rows={3}
            className="w-full resize-none rounded-lg border border-brand-border bg-brand-bg px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand-accent focus:outline-none"
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              {DEMO_QUERIES.map((q) => (
                <button
                  type="button"
                  key={q}
                  onClick={() => {
                    setQuestion(q);
                    ask(q);
                  }}
                  className="rounded-full border border-brand-border bg-brand-bg px-3 py-1 text-xs text-slate-300 transition-colors hover:border-brand-accent hover:text-brand-accent"
                >
                  {q}
                </button>
              ))}
            </div>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="shrink-0 rounded-lg bg-brand-accent px-5 py-2 text-sm font-semibold text-brand-bg transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? "Thinking…" : "Ask OpsBrain"}
            </button>
          </div>
        </form>
      </SectionCard>

      {loading && (
        <SectionCard title="Answer">
          <LoadingBlock label="Retrieving evidence and composing a cited answer…" />
        </SectionCard>
      )}

      {!loading && error && (
        <SectionCard title="Answer">
          <p className="text-sm text-brand-danger">{error}</p>
        </SectionCard>
      )}

      {!loading && !error && !answer && (
        <SectionCard title="Answer">
          <EmptyBlock label="Ask a question above, or pick one of the suggested prompts, to see a cited answer." />
        </SectionCard>
      )}

      {!loading && !error && answer && (
        <div className="space-y-6">
          <SectionCard
            title="Answer"
            subtitle={source === "mock" ? "Demo Mode — seeded mock answer (backend unreachable)" : undefined}
            action={<ConfidenceMeter score={answer.confidence_score} />}
          >
            <p className="text-sm leading-relaxed text-slate-100">{answer.answer}</p>

            {answer.supporting_entities.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {answer.supporting_entities.map((e) => (
                  <span
                    key={e.id}
                    className="rounded-full border border-brand-border bg-brand-bg px-2.5 py-1 text-xs text-slate-300"
                  >
                    <span className="text-slate-500">{e.type}</span> · {e.label}
                  </span>
                ))}
              </div>
            )}

            <button
              onClick={() => setShowWhy((v) => !v)}
              className="mt-4 text-xs font-medium text-brand-accent hover:underline"
            >
              {showWhy ? "Hide" : "Show"} why this answer ▾
            </button>

            {showWhy && (
              <div className="mt-3 rounded-lg border border-brand-border bg-brand-bg/60 p-4 text-sm text-slate-300">
                <p>
                  OpsBrain retrieved <strong>{answer.citations.length}</strong> supporting passage
                  {answer.citations.length === 1 ? "" : "s"} from{" "}
                  <strong>{answer.supporting_documents.length}</strong> document
                  {answer.supporting_documents.length === 1 ? "" : "s"}, and matched{" "}
                  <strong>{answer.supporting_entities.length}</strong> known entit
                  {answer.supporting_entities.length === 1 ? "y" : "ies"} in the knowledge graph
                  (assets, failure modes, incidents, or regulations mentioned in your question).
                  The confidence score ({Math.round(answer.confidence_score * 100)}%) reflects how
                  directly those passages address the question and how many independent documents
                  agree with each other.
                </p>
                <div className="mt-3 space-y-2">
                  {answer.citations.map((c, i) => (
                    <CitationChip key={`${c.document_id}-${i}`} citation={c} index={i} />
                  ))}
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard title="Recommended Actions">
            {answer.recommended_actions.length === 0 ? (
              <EmptyBlock label="No specific actions recommended." />
            ) : (
              <ul className="space-y-3">
                {answer.recommended_actions.map((a, i) => (
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

          <SectionCard title="Citations">
            <div className="grid gap-2 md:grid-cols-2">
              {answer.citations.map((c, i) => (
                <CitationChip key={`${c.document_id}-full-${i}`} citation={c} index={i} />
              ))}
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}

export default function CopilotPage() {
  return (
    <Suspense fallback={<LoadingBlock label="Loading Copilot…" />}>
      <CopilotBody />
    </Suspense>
  );
}
