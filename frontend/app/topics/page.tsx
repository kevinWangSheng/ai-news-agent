"use client";
import Link from "next/link";
import { useTopics } from "@/lib/api/hooks";

export default function TopicsPage() {
  const { data, error, isLoading } = useTopics();
  if (isLoading) return <p className="text-sm text-neutral-500">加载中…</p>;
  if (error) return <p className="text-sm text-red-500">{String(error)}</p>;
  const topics = data ?? [];
  return (
    <section>
      <h1 className="text-2xl font-semibold mb-4">主题</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {topics.map((t) => (
          <Link
            key={t.slug}
            href={`/topics/${t.slug}`}
            className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-3 hover:bg-neutral-50 dark:hover:bg-neutral-900/40"
          >
            <div className="flex items-baseline justify-between">
              <h2 className="font-medium">{t.name_zh}</h2>
              <span className="text-xs text-neutral-500">{t.item_count}</span>
            </div>
            <p className="text-xs text-neutral-500 mt-1">#{t.slug}</p>
            {t.last_item_at && <p className="text-xs text-neutral-400 mt-1">最近 {t.last_item_at.slice(0, 10)}</p>}
          </Link>
        ))}
      </div>
    </section>
  );
}
