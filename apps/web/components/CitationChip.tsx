import type { Citation } from "@shared/types";

export function CitationChip({ citation, index }: { citation: Citation; index: number }) {
  return (
    <div className="rounded-lg border border-brand-border bg-brand-bg/60 px-3 py-2 text-xs">
      <div className="flex items-center gap-2 text-slate-300">
        <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-brand-accent/20 text-[10px] font-semibold text-brand-accent">
          {index + 1}
        </span>
        <span className="font-medium text-slate-200">{citation.document_title}</span>
      </div>
      <p className="mt-1.5 pl-6 text-slate-400">&ldquo;{citation.snippet}&rdquo;</p>
    </div>
  );
}
