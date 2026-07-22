import type { ReactNode } from "react";

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-slate-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-border border-t-brand-accent" />
      {label}
    </div>
  );
}

export function EmptyBlock({ label = "Nothing here yet." }: { label?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-brand-border py-8 text-center text-sm text-slate-500">
      {label}
    </div>
  );
}

export function ErrorBlock({ label = "Something went wrong." }: { label?: string }) {
  return (
    <div className="rounded-lg border border-brand-danger/40 bg-brand-danger/10 py-6 text-center text-sm text-brand-danger">
      {label}
    </div>
  );
}

/** Generic loading/error/empty wrapper so screens don't re-implement this switch
 * every time — a hard requirement per MASTER_SPEC §13 (never a blank/broken screen). */
export function AsyncSection<T>({
  loading,
  error,
  data,
  isEmpty,
  loadingLabel,
  emptyLabel,
  errorLabel,
  children,
}: {
  loading: boolean;
  error?: string | null;
  data: T;
  isEmpty?: (data: T) => boolean;
  loadingLabel?: string;
  emptyLabel?: string;
  errorLabel?: string;
  children: (data: T) => ReactNode;
}) {
  if (loading) return <LoadingBlock label={loadingLabel} />;
  if (error) return <ErrorBlock label={errorLabel ?? error} />;
  if (isEmpty?.(data)) return <EmptyBlock label={emptyLabel} />;
  return <>{children(data)}</>;
}
