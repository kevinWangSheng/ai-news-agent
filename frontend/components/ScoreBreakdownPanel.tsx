function n(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

export function ScoreBreakdownPanel({ breakdown, score }: { breakdown?: Record<string, unknown> | null; score?: number | null }) {
  if (!breakdown && score == null) return null;
  const base = n(breakdown?.base);
  const final = n(breakdown?.final ?? score ?? 0);
  const rows = [
    ["基础分", base],
    ["主题加权", n(breakdown?.tag_boost)],
    ["信源加权", n(breakdown?.source_boost)],
    ["实体加权", n(breakdown?.entity_boost)],
    ["时间衰减", n(breakdown?.time_decay)],
  ] as const;
  const focusHits = Array.isArray(breakdown?.focus_hits) ? (breakdown?.focus_hits as string[]) : [];
  const cold = Boolean(breakdown?.cold_start);

  return (
    <section className="mt-6 rounded-xl border border-amber-200 bg-amber-50/60 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold text-amber-900 dark:text-amber-100">为什么看到这条</h2>
        <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-200">评分 {final.toFixed(1)}</span>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-5">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg bg-white/70 p-2 dark:bg-neutral-950/40">
            <div className="text-[11px] text-neutral-500">{label}</div>
            <div className="font-mono text-sm">{value >= 0 ? "+" : ""}{value.toFixed(1)}</div>
          </div>
        ))}
      </div>
      {focusHits.length > 0 && <p className="mt-3 text-xs text-neutral-600 dark:text-neutral-300">匹配关键词：{focusHits.map((x) => `#${x}`).join(" ")}</p>}
      {cold && <p className="mt-2 text-xs text-red-600 dark:text-red-300">⚠ 冷启动中：交互数还没到阈值，推荐权重尚未完全启用。</p>}
    </section>
  );
}
