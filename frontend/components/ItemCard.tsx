"use client";
import Link from "next/link";
import type { Item } from "@/lib/api/hooks";

export function ItemCard({
  item,
  onKeep,
  onArchive,
  onTrash,
}: {
  item: Item;
  onKeep?: () => void;
  onArchive?: () => void;
  onTrash?: () => void;
}) {
  return (
    <article className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4 hover:bg-neutral-50 dark:hover:bg-neutral-900/40 transition">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <Link href={`/item/${item.id}`} className="font-medium hover:underline">
            {item.title_cn || item.title || "(无标题)"}
          </Link>
          {item.summary_zh && (
            <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400 line-clamp-3">
              {item.summary_zh}
            </p>
          )}
          <div className="mt-2 flex items-center gap-2 text-xs text-neutral-500 flex-wrap">
            <span>{item.source_name || item.source_type}</span>
            {item.author && <span>· {item.author}</span>}
            {item.published_at && <span>· {item.published_at.slice(0, 10)}</span>}
            {item.final_score !== null && (
              <span className="px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800">
                {item.final_score.toFixed(1)}
              </span>
            )}
            {(item.tags || []).slice(0, 5).map((t) => (
              <span key={t} className="px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300">
                #{t}
              </span>
            ))}
          </div>
        </div>
        <div className="flex gap-1 shrink-0">
          {onKeep && <button onClick={onKeep} className="text-xs px-2 py-1 rounded bg-green-100 hover:bg-green-200 dark:bg-green-900/40 dark:hover:bg-green-900/60">保留</button>}
          {onArchive && <button onClick={onArchive} className="text-xs px-2 py-1 rounded bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700">归档</button>}
          {onTrash && <button onClick={onTrash} className="text-xs px-2 py-1 rounded bg-red-100 hover:bg-red-200 dark:bg-red-900/40 dark:hover:bg-red-900/60">删除</button>}
        </div>
      </div>
    </article>
  );
}
