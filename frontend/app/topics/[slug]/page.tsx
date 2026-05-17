"use client";
import { use } from "react";
import useSWR from "swr";
import type { Item } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

export default function TopicDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { data: items } = useSWR<Item[]>(`/api/topics/${slug}/items?limit=100`);
  const { data: timeline } = useSWR<{ bucket: string; count: number }[]>(`/api/topics/${slug}/timeline?bucket=month`);

  return (
    <section>
      <h1 className="text-2xl font-semibold mb-1">#{slug}</h1>
      <p className="text-sm text-neutral-500 mb-4">{items?.length ?? 0} 条相关</p>

      {timeline && timeline.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-medium mb-2">时间线(按月)</h2>
          <div className="flex items-end gap-1 h-24 border-b border-l border-neutral-200 dark:border-neutral-800 pl-2 pb-1">
            {[...timeline].reverse().map((b) => (
              <div key={b.bucket} className="flex flex-col items-center gap-1">
                <div className="w-6 bg-blue-500/70 dark:bg-blue-400/70 rounded-t" style={{ height: `${Math.min(80, b.count * 4)}px` }} title={`${b.count}`} />
                <span className="text-[10px] text-neutral-500">{b.bucket?.slice(0, 7) ?? "-"}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {(items ?? []).map((it) => <ItemCard key={it.id} item={it} />)}
      </div>
    </section>
  );
}
