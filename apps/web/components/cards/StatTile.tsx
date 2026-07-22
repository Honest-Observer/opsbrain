import type { ReactNode } from "react";
import { cx } from "@/lib/utils";

type Tone = "default" | "accent" | "warn" | "danger";

const TONE_STYLES: Record<Tone, string> = {
  default: "text-slate-100",
  accent: "text-brand-accent",
  warn: "text-brand-warn",
  danger: "text-brand-danger",
};

export function StatTile({
  label,
  value,
  sub,
  tone = "default",
  icon,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: Tone;
  icon?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-brand-border bg-brand-panel px-5 py-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
        {icon ? <div className="text-slate-500">{icon}</div> : null}
      </div>
      <p className={cx("mt-2 text-2xl font-semibold tabular-nums", TONE_STYLES[tone])}>{value}</p>
      {sub ? <p className="mt-1 text-xs text-slate-500">{sub}</p> : null}
    </div>
  );
}
