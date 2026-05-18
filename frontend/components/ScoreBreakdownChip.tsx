function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function ScoreBreakdownChip({ breakdown, score }: { breakdown?: Record<string, unknown> | null; score?: number | null }) {
  if (!breakdown && score == null) return null;
  const base = num(breakdown?.base);
  const final = num(breakdown?.final) ?? score ?? null;
  const parts: string[] = [];
  const tag = num(breakdown?.tag_boost);
  const source = num(breakdown?.source_boost);
  const entity = num(breakdown?.entity_boost);
  if (base != null) parts.push(`${base.toFixed(1)} base`);
  if (tag) parts.push(`+${tag.toFixed(1)} topic`);
  if (source) parts.push(`+${source.toFixed(1)} source`);
  if (entity) parts.push(`+${entity.toFixed(1)} entity`);
  const focus = Array.isArray(breakdown?.focus_hits) ? (breakdown?.focus_hits as unknown[]).slice(0, 2).join(" #") : "";
  return (
    <span className="inline-flex max-w-full items-center truncate rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] text-neutral-500 opacity-0 transition group-hover:opacity-100 dark:bg-neutral-800 dark:text-neutral-400">
      {final != null ? final.toFixed(1) : "score"} = {parts.join(" ") || "breakdown"}{focus ? ` · #${focus}` : ""}
    </span>
  );
}
