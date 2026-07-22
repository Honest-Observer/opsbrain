"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { cx } from "@/lib/utils";
import { DemoModeBanner } from "./DemoModeBanner";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", hint: "Overview" },
  { href: "/ingest", label: "Ingest", hint: "Upload raw data" },
  { href: "/copilot", label: "Copilot", hint: "Ask a question" },
  { href: "/assets/P-101", label: "Asset 360", hint: "Per-asset deep dive" },
  { href: "/graph", label: "Graph Explorer", hint: "Knowledge graph" },
  { href: "/compliance", label: "Compliance Board", hint: "Evidence gaps" },
  { href: "/lessons", label: "Lessons Learned", hint: "Prevention feed" },
  { href: "/evaluation", label: "Evaluation", hint: "Benchmark quality" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r border-brand-border bg-brand-panel">
        <div className="border-b border-brand-border px-5 py-5">
          <Link href="/dashboard" className="block">
            <span className="text-lg font-bold tracking-tight text-slate-50">
              Ops<span className="text-brand-accent">Brain</span>
            </span>
          </Link>
          <p className="mt-1 text-xs text-slate-500">Industrial Knowledge &amp; Operations Brain</p>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href.split("/").slice(0, 2).join("/")));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cx(
                  "flex flex-col rounded-lg px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-brand-accent/10 text-brand-accent"
                    : "text-slate-300 hover:bg-brand-bg hover:text-slate-100"
                )}
              >
                <span className="font-medium">{item.label}</span>
                <span className="text-xs text-slate-500">{item.hint}</span>
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-brand-border px-5 py-4 text-xs text-slate-500">
          Prototype build — ET AI Hackathon 2026
        </div>
      </aside>
      <div className="flex min-h-screen flex-1 flex-col">
        <DemoModeBanner />
        <main className="flex-1 overflow-x-hidden px-6 py-6 md:px-10 md:py-8">{children}</main>
      </div>
    </div>
  );
}
