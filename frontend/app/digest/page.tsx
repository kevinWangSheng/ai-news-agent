"use client";
import useSWR from "swr";

type Digest = { id: number; period: string; period_key: string; title: string | null; intro: string | null; item_ids: number[]; generated_at: string };

export default function DigestPage() {
  const { data, isLoading } = useSWR<Digest[]>("/api/digests");
  if (isLoading) return <p className="text-sm text-neutral-500">加载中…</p>;
  const digests = data ?? [];
  return (
    <section>
      <h1 className="text-2xl font-semibold mb-4">精选</h1>
      {digests.length === 0 && (
        <p className="text-sm text-neutral-500">还没有精选;由 scheduler 每日 06:30 / 每周一 06:30 生成,也可在 settings 手动触发</p>
      )}
      <div className="space-y-3">
        {digests.map((d) => (
          <article key={d.id} className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4">
            <div className="flex items-baseline justify-between">
              <h2 className="font-medium">{d.title || `${d.period} · ${d.period_key}`}</h2>
              <span className="text-xs text-neutral-500">{d.generated_at.slice(0, 10)}</span>
            </div>
            {d.intro && <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">{d.intro}</p>}
            <p className="mt-2 text-xs text-neutral-500">{d.item_ids?.length ?? 0} 条入选</p>
          </article>
        ))}
      </div>
    </section>
  );
}
