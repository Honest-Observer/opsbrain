import type { ReactNode } from "react";
import { cx } from "@/lib/utils";

export function SectionCard({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx("rounded-xl border border-brand-border bg-brand-panel", className)}>
      <header className="flex items-start justify-between gap-4 border-b border-brand-border px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-slate-100">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </header>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}
