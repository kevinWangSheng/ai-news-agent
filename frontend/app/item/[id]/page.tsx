"use client";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useItem, patchItem, recordInteraction } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { ScoreBreakdownPanel } from "@/components/ScoreBreakdownPanel";
import { TierBadge } from "@/components/TierBadge";
import { ReadingTimeBadge } from "@/components/ReadingTimeBadge";

export default function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const itemId = Number(id);
  const { data: item, isLoading, mutate } = useItem(itemId);
  const [note, setNote] = useState("");
  const [savingNote, setSavingNote] = useState(false);

  useEffect(() => {
    if (item) recordInteraction(item.id, "view").catch(() => {});
  }, [item?.id]);

  useEffect(() => {
    if (item) setNote(item.user_note || "");
  }, [item?.id, item?.user_note]);

  if (isLoading) return <p className="text-sm text-neutral-500">加载中…</p>;
  if (!item) return <p className="text-sm text-neutral-500">未找到</p>;

  async function saveNote() {
    if (!item) return;
    setSavingNote(true);
    try {
      await recordInteraction(item.id, "note", { note_text: note });
      await patchItem(item.id, { user_note: note });
      mutate();
    } finally {
      setSavingNote(false);
    }
  }

  return (
    <article className="mx-auto max-w-4xl">
      <div className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <div className="flex flex-wrap items-center gap-2">
          <TierBadge item={item} />
          <ReadingTimeBadge content={item.content_md || item.summary_zh || item.summary_en || item.title} />
          {item.final_score !== null && <span className="rounded-full bg-neutral-100 px-2 py-0.5 font-mono text-xs dark:bg-neutral-800">score {item.final_score.toFixed(1)}</span>}
        </div>
        <h1 className="mt-4 text-3xl font-semibold leading-tight tracking-tight">{item.title_cn || item.title || "(无标题)"}</h1>
        {item.url && (
          <p className="mt-2 truncate text-xs">
            <a className="text-blue-600 underline dark:text-blue-400" href={item.url} target="_blank" rel="noreferrer">{item.url}</a>
          </p>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-neutral-500">
          <span>{item.source_name || item.source_type}</span>
          {item.author && <span>· {item.author}</span>}
          {item.published_at && <span>· {item.published_at.slice(0, 10)}</span>}
          {item.viewed_at && <span>· 已读 {item.viewed_at.slice(0, 10)}</span>}
        </div>
      </div>

      {item.summary_zh && (
        <section className="mt-6 rounded-2xl bg-neutral-50 p-5 dark:bg-neutral-900/50">
          <h2 className="text-sm font-medium text-neutral-500">摘要</h2>
          <p className="mt-2 leading-7">{item.summary_zh}</p>
        </section>
      )}
      {item.recommendation && (
        <section className="mt-4 rounded-2xl border border-blue-100 bg-blue-50/60 p-5 dark:border-blue-950/60 dark:bg-blue-950/20">
          <h2 className="text-sm font-medium text-blue-700 dark:text-blue-300">推荐理由</h2>
          <p className="mt-2 text-sm leading-6">{item.recommendation}</p>
        </section>
      )}

      <ScoreBreakdownPanel breakdown={item.score_breakdown} score={item.final_score} />

      <div className="mt-6 flex gap-2">
        <button onClick={async () => { await recordInteraction(item.id, "keep"); mutate(); }} className="rounded-lg bg-green-100 px-3 py-2 text-sm text-green-800 dark:bg-green-900/40 dark:text-green-200">保留</button>
        <button onClick={async () => { await patchItem(item.id, { status: "archived" }); mutate(); }} className="rounded-lg bg-neutral-100 px-3 py-2 text-sm dark:bg-neutral-800">归档</button>
        <button onClick={async () => { await patchItem(item.id, { status: "trashed" }); mutate(); }} className="rounded-lg bg-red-100 px-3 py-2 text-sm text-red-800 dark:bg-red-900/40 dark:text-red-200">删除</button>
      </div>

      {(item.topics?.length || item.entities?.length) ? (
        <section className="mt-6 flex flex-wrap gap-2">
          {item.topics?.map((t) => <Link key={t.slug} href={`/topics/${t.slug}`} className="rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-700 dark:bg-blue-950/40 dark:text-blue-300">#{t.name_zh}</Link>)}
          {item.entities?.map((e) => <Link key={e.slug} href={`/entities/${e.slug}`} className="rounded-full bg-purple-50 px-3 py-1 text-xs text-purple-700 dark:bg-purple-950/40 dark:text-purple-300">@{e.name}</Link>)}
        </section>
      ) : null}

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-medium text-neutral-500">正文</h2>
        <MarkdownRenderer source={item.content_md || item.summary_en || item.summary_zh} />
      </section>

      <section className="mt-8 rounded-2xl border border-neutral-200 p-4 dark:border-neutral-800">
        <h2 className="text-sm font-medium">我的笔记</h2>
        <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="这条对我有什么用？" className="mt-3 min-h-28 w-full rounded-xl border border-neutral-200 bg-white p-3 text-sm outline-none focus:border-blue-400 dark:border-neutral-800 dark:bg-neutral-950" />
        <div className="mt-3 flex justify-end">
          <button onClick={saveNote} disabled={savingNote} className="rounded-lg bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-50 dark:bg-white dark:text-neutral-900">{savingNote ? "保存中…" : "保存笔记"}</button>
        </div>
      </section>

      {item.related_items?.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-sm font-medium text-neutral-500">相关</h2>
          <div className="space-y-3">{item.related_items.map((r) => <ItemCard key={r.id} item={r} />)}</div>
        </section>
      )}
    </article>
  );
}
