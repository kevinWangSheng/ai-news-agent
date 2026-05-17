"use client";
import { useItems, patchItem, recordInteraction } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

export default function InboxPage() {
  const { data, error, isLoading, mutate } = useItems({ status: "inbox", limit: 50 });
  if (isLoading) return <p className="text-sm text-neutral-500">加载中…</p>;
  if (error) return <p className="text-sm text-red-500">{String(error)}</p>;
  const items = data?.items ?? [];
  return (
    <section>
      <header className="mb-4 flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold">Inbox</h1>
        <span className="text-sm text-neutral-500">{items.length} 条待处理</span>
      </header>
      <div className="space-y-3">
        {items.map((it) => (
          <ItemCard
            key={it.id}
            item={it}
            onKeep={async () => { await recordInteraction(it.id, "keep"); mutate(); }}
            onArchive={async () => { await patchItem(it.id, { status: "archived" }); mutate(); }}
            onTrash={async () => { await patchItem(it.id, { status: "trashed" }); mutate(); }}
          />
        ))}
        {items.length === 0 && <p className="text-sm text-neutral-500">Inbox 是空的 🎉</p>}
      </div>
    </section>
  );
}
