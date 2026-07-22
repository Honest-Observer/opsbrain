import { cx, formatPercent } from "@/lib/utils";

export function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(1, score));
  const tone = pct >= 0.75 ? "bg-brand-accent" : pct >= 0.5 ? "bg-brand-warn" : "bg-brand-danger";
  return (
    <div className="w-full max-w-[220px]">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Confidence</span>
        <span className="font-semibold text-slate-200">{formatPercent(pct)}</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-brand-border">
        <div className={cx("h-full rounded-full", tone)} style={{ width: `${pct * 100}%` }} />
      </div>
    </div>
  );
}
