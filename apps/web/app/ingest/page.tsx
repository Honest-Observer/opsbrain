"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { SectionCard } from "@/components/cards/SectionCard";
import { useHealth } from "@/components/DemoModeBanner";
import { uploadDocument, type UploadResult } from "@/lib/api";

interface UploadRow extends UploadResult {
  filename: string;
  status: "done" | "error";
  error?: string;
}

export default function IngestPage() {
  const [, health] = useHealth();
  const gemini = health?.ai_mode === "gemini";
  const [rows, setRows] = useState<UploadRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setBusy(true);
    for (const file of Array.from(files)) {
      try {
        const res = await uploadDocument(file);
        setRows((prev) => [{ ...res, filename: file.name, status: "done" }, ...prev]);
      } catch (e) {
        setRows((prev) => [
          {
            filename: file.name,
            status: "error",
            document_id: "",
            chunks_created: 0,
            error: e instanceof Error ? e.message : String(e),
          },
          ...prev,
        ]);
      }
    }
    setBusy(false);
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Ingest raw plant data"
        description="Drop in any industrial document — SOPs, work orders, inspection reports, incident logs, CSV/XLSX registries, handover notes, PDFs. OpsBrain parses it, embeds it for semantic search, and (with Gemini) extracts entities and relationships into the live knowledge graph so you can immediately ask questions about it."
      />

      <div
        className={
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors " +
          (dragOver ? "border-brand-accent bg-brand-accent/5" : "border-brand-border bg-brand-panel")
        }
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        <p className="text-sm text-slate-300">
          Drag &amp; drop files here, or{" "}
          <button
            type="button"
            className="font-medium text-brand-accent underline-offset-2 hover:underline"
            onClick={() => inputRef.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="mt-2 text-xs text-slate-500">
          Supports PDF, TXT, MD, CSV, XLSX, JSON, and scanned-form text.
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
          accept=".pdf,.txt,.md,.csv,.xlsx,.json"
        />
        {busy ? <p className="mt-4 text-xs text-brand-accent">Processing… parsing, embedding, extracting graph.</p> : null}
      </div>

      <div className="mt-4 rounded-lg border border-brand-border bg-brand-panel px-4 py-3 text-xs">
        {gemini ? (
          <span className="text-brand-accent">
            Gemini extraction is live ({health?.ai_model}) — uploads build real entities &amp; graph edges and become
            fully queryable.
          </span>
        ) : (
          <span className="text-slate-400">
            Offline heuristic mode — uploads are parsed, embedded, and regex-extracted. Add a{" "}
            <code className="text-slate-300">GEMINI_API_KEY</code> to enable full LLM graph extraction over arbitrary
            documents.
          </span>
        )}
      </div>

      {rows.length > 0 ? (
        <SectionCard title="Ingested this session" className="mt-6">
          <ul className="divide-y divide-brand-border">
            {rows.map((row, i) => (
              <li key={i} className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-100">{row.filename}</p>
                  {row.status === "done" ? (
                    <p className="mt-0.5 text-xs text-slate-500">
                      {row.chunks_created} chunk(s)
                      {typeof row.entities_created === "number" ? ` · ${row.entities_created} entities` : ""}
                      {typeof row.relationships_created === "number" ? ` · ${row.relationships_created} relationships` : ""}
                      {row.ai_mode ? ` · ${row.ai_mode === "gemini" ? "Gemini" : "heuristic"} extraction` : ""}
                    </p>
                  ) : (
                    <p className="mt-0.5 text-xs text-brand-danger">{row.error}</p>
                  )}
                </div>
                {row.status === "done" ? (
                  <span className="rounded-full border border-brand-accent/40 bg-brand-accent/10 px-2 py-0.5 text-xs font-medium text-brand-accent">
                    Ingested
                  </span>
                ) : (
                  <span className="rounded-full border border-brand-danger/40 bg-brand-danger/10 px-2 py-0.5 text-xs font-medium text-brand-danger">
                    Failed
                  </span>
                )}
              </li>
            ))}
          </ul>
          <div className="mt-4 border-t border-brand-border pt-4 text-sm text-slate-400">
            New data is live. Head to the{" "}
            <Link href="/copilot" className="font-medium text-brand-accent hover:underline">
              Copilot
            </Link>{" "}
            and ask about what you just uploaded, or open the{" "}
            <Link href="/graph" className="font-medium text-brand-accent hover:underline">
              Graph Explorer
            </Link>{" "}
            to see the new entities.
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
