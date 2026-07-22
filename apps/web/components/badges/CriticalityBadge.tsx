import { cx } from "@/lib/utils";

type Criticality = "low" | "medium" | "high" | "critical";

const STYLES: Record<Criticality, string> = {
  critical: "bg-brand-danger/20 text-brand-danger border-brand-danger/50",
  high: "bg-brand-warn/15 text-brand-warn border-brand-warn/40",
  medium: "bg-sky-500/15 text-sky-300 border-sky-500/40",
  low: "bg-slate-500/15 text-slate-300 border-slate-500/40",
};

export function CriticalityBadge({ criticality, className }: { criticality: Criticality; className?: string }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        STYLES[criticality],
        className
      )}
    >
      {criticality}
    </span>
  );
}
