import { cx } from "@/lib/utils";

type Severity = "low" | "medium" | "high";

const STYLES: Record<Severity, string> = {
  high: "bg-brand-danger/15 text-brand-danger border-brand-danger/40",
  medium: "bg-brand-warn/15 text-brand-warn border-brand-warn/40",
  low: "bg-brand-accent/15 text-brand-accent border-brand-accent/40",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        STYLES[severity],
        className
      )}
    >
      {severity}
    </span>
  );
}
