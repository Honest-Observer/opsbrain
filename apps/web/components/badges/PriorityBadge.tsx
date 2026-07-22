import { cx } from "@/lib/utils";

type Priority = "low" | "medium" | "high";

const STYLES: Record<Priority, string> = {
  high: "bg-brand-danger/15 text-brand-danger border-brand-danger/40",
  medium: "bg-brand-warn/15 text-brand-warn border-brand-warn/40",
  low: "bg-slate-500/15 text-slate-300 border-slate-500/40",
};

export function PriorityBadge({ priority, className }: { priority: Priority; className?: string }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        STYLES[priority],
        className
      )}
    >
      {priority} priority
    </span>
  );
}
