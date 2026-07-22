import { cx } from "@/lib/utils";

type ComplianceStatus = "ok" | "gap" | "at_risk";

const STYLES: Record<ComplianceStatus, string> = {
  ok: "bg-brand-accent/15 text-brand-accent border-brand-accent/40",
  at_risk: "bg-brand-warn/15 text-brand-warn border-brand-warn/40",
  gap: "bg-brand-danger/15 text-brand-danger border-brand-danger/40",
};

const LABELS: Record<ComplianceStatus, string> = {
  ok: "OK",
  at_risk: "At Risk",
  gap: "Gap",
};

export function StatusBadge({ status, className }: { status: ComplianceStatus; className?: string }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        STYLES[status],
        className
      )}
    >
      {LABELS[status]}
    </span>
  );
}
