"use client";

import { useEffect, useState } from "react";
import { checkHealth, type HealthResponse } from "@/lib/api";

type Status = "checking" | "online" | "offline";

export function useBackendStatus(): Status {
  const [status] = useHealth();
  return status;
}

export function useHealth(): [Status, HealthResponse | null] {
  const [status, setStatus] = useState<Status>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      const res = await checkHealth();
      if (cancelled) return;
      setStatus(res.source === "live" ? "online" : "offline");
      setHealth(res.data);
    }
    poll();
    const id = setInterval(poll, 30000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return [status, health];
}

export function DemoModeBanner() {
  const [status, health] = useHealth();

  if (status === "checking") return null;
  if (status === "online") {
    const gemini = health?.ai_mode === "gemini";
    return (
      <div className="flex items-center gap-3 border-b border-brand-border bg-brand-panel px-4 py-1.5 text-xs text-slate-400">
        <span className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />
          Live backend connected
        </span>
        <span
          className={
            gemini
              ? "flex items-center gap-1.5 rounded-full border border-brand-accent/40 bg-brand-accent/10 px-2 py-0.5 font-medium text-brand-accent"
              : "flex items-center gap-1.5 rounded-full border border-brand-border px-2 py-0.5 text-slate-400"
          }
          title={health?.ai_model ? `Model: ${health.ai_model}` : undefined}
        >
          <span className={gemini ? "h-1.5 w-1.5 rounded-full bg-brand-accent" : "h-1.5 w-1.5 rounded-full bg-slate-500"} />
          {gemini ? `Gemini AI: Live (${health?.ai_model})` : "Offline heuristic mode"}
        </span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 border-b border-brand-border bg-brand-warn/10 px-4 py-1.5 text-xs text-brand-warn">
      <span className="h-1.5 w-1.5 rounded-full bg-brand-warn" />
      Demo Mode — backend unreachable at :8000, showing seeded mock data so the demo keeps working.
    </div>
  );
}
