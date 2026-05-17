"use client";
import Link from "next/link";
import { use, useEffect } from "react";
import { useItem, patchItem, recordInteraction } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

export default function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const itemId = Number(id);
  const { data: item, isLoading, mutate } = useItem(itemId);

  useEffect(() => {
    if (item) recordInteraction(item.id, "view").catch(() => {});
  }, [item?.id]);

  if (isLoading) return <p className="text-sm text-neutral-500">加载中…</p>;
  if (!item) return <p className="text-sm text-neutral-500">未找到</p>;

  return (
    <article className="max-w-3xl">
      <h1 className="text-2xl font-semibold">{item.title_cn || item.title || "(无标题)"}</h1>
      {item.url && (
        <p className="text-xs mt-1">
          <a className="text-blue-600 dark:text-blue-400 underline" href={item.url} target="_blank" rel="noreferrer">
            {item.url}
          </a>
        </p>
      )}
      <div className="mt-3 flex items-center gap-2 text-xs text-neutral-500 flex-wrap">
        <span>{item.source_name || item.source_type}</span>
        {item.author && <span>· {item.author}</span>}
        {item.published_at && <span>· {item.published_at.slice(0, 10)}</span>}
        {item.final_score !== null && <span>score {item.final_score.toFixed(1)}</span>}
      </div>

      {item.summary_zh && (
        <section className="mt-4">
          <h2 className="text-sm font-medium text-neutral-500">摘要</h2>
          <p className="text-base mt-1">{item.summary_zh}</p>
        </section>
      )}
      {item.recommendation && (
        <section className="mt-4">
          <h2 className="text-sm font-medium text-neutral-500">推荐理由</h2>
          <p className="text-sm mt-1">{item.recommendation}</p>
        </section>
      )}

      <div className="mt-4 flex gap-2">
        <button onClick={async () => { await patchItem(item.id, { status: "kept" }); mutate(); }} className="text-xs px-2 py-1 rounded bg-green-100 dark:bg-green-900/40">保留</button>
        <button onClick={async () => { await patchItem(item.id, { status: "archived" }); mutate(); }} className="text-xs px-2 py-1 rounded bg-neutral-100 dark:bg-neutral-800">归档</button>
        <button onClick={async () => { await patchItem(item.id, { status: "trashed" }); mutate(); }} className="text-xs px-2 py-1 rounded bg-red-100 dark:bg-red-900/40">删除</button>
      </div>

      {(item.topics?.length || item.entities?.length) ? (
        <section className="mt-6 flex flex-wrap gap-2">
          {item.topics?.map((t) => (
            <Link key={t.slug} href={`/topics/${t.slug}`} className="text-xs px-2 py-1 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300">#{t.name_zh}</Link>
          ))}
          {item.entities?.map((e) => (
            <Link key={e.slug} href={`/entities/${e.slug}`} className="text-xs px-2 py-1 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300">@{e.name}</Link>
          ))}
        </section>
      ) : null}

      {item.content_md && (
        <section className="mt-6">
          <h2 className="text-sm font-medium text-neutral-500 mb-2">正文</h2>
          <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap text-sm">{item.content_md}</div>
        </section>
      )}

      {item.related_items?.length > 0 && (
        <section className="mt-8">
          <h2 className="text-sm font-medium text-neutral-500 mb-2">相关</h2>
          <div className="space-y-2">
            {item.related_items.map((r) => <ItemCard key={r.id} item={r} />)}
          </div>
        </section>
      )}
    </article>
  );
}
