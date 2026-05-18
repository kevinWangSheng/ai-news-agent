"use client";
import Link from "next/link";
import type { MouseEvent } from "react";
import type { Item } from "@/lib/api/hooks";
import { slugify } from "@/lib/slugify";
import { estimateMinutes } from "@/lib/readingTime";
import { TierBadge } from "@/components/TierBadge";
import { ScoreBreakdownChip } from "@/components/ScoreBreakdownChip";

export type ItemVariant = "top" | "hot" | "normal" | "dim";

function autoVariant(item: Item): ItemVariant {
  if (item.viewed_at) return "dim";
  const score = item.final_score ?? 0;
  if (score >= 10) return "top";
  if (score >= 9) return "hot";
  if (score > 0 && score < 7) return "dim";
  return "normal";
}

function isNew(item: Item) {
  return Date.now() - new Date(item.ingested_at).getTime() <= 24 * 60 * 60 * 1000;
}

const shell: Record<ItemVariant, string> = {
  top: "border-2 border-amber-400 p-5 shadow-md shadow-amber-100/50 dark:border-amber-500 dark:shadow-none",
  hot: "border border-orange-300 p-4 shadow-sm dark:border-orange-700",
  normal: "border border-neutral-200 p-4 dark:border-neutral-800",
  dim: "border border-neutral-200/60 p-3 opacity-70 dark:border-neutral-800/60",
};

const title: Record<ItemVariant, string> = {
  top: "text-lg font-semibold leading-snug",
  hot: "text-base font-semibold leading-snug",
  normal: "font-medium leading-snug",
  dim: "text-sm font-medium leading-snug",
};

export function ItemCard({
  item,
  variant,
  selected = false,
  focused = false,
  onSelect,
  onKeep,
  onArchive,
  onTrash,
}: {
  item: Item;
  variant?: ItemVariant;
  selected?: boolean;
  focused?: boolean;
  onSelect?: (shift: boolean, meta: boolean) => void;
  onKeep?: () => void;
  onArchive?: () => void;
  onTrash?: () => void;
}) {
  const v = variant ?? autoVariant(item);
  const score = item.final_score ?? 0;
  const bodyText = [item.summary_zh, item.summary_en, item.recommendation, item.title, item.title_cn].filter(Boolean).join("\n");
  const emojis = [score >= 10 ? "⭐" : score >= 9 ? "🔥" : "", isNew(item) ? "🆕" : ""].filter(Boolean);

  function handleClick(e: MouseEvent<HTMLElement>) {
    if (!onSelect || e.defaultPrevented) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey) {
      e.preventDefault();
      onSelect(e.shiftKey, e.metaKey || e.ctrlKey);
    }
  }

  return (
    <article
      onClick={handleClick}
      className={`group relative rounded-2xl bg-white transition hover:-translate-y-0.5 hover:bg-neutral-50 dark:bg-neutral-950 dark:hover:bg-neutral-900/60 ${shell[v]} ${selected ? "ring-2 ring-blue-400" : ""} ${focused ? "outline outline-2 outline-offset-2 outline-blue-400" : ""}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <TierBadge item={item} compact />
            {emojis.map((emoji) => <span key={emoji} className="text-xs">{emoji}</span>)}
            {score > 0 && <span className="rounded-full bg-neutral-100 px-2 py-0.5 font-mono text-[11px] text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300">{score.toFixed(1)}</span>}
          </div>
          <Link href={`/item/${item.id}`} className={`${title[v]} hover:underline`}>
            {item.title_cn || item.title || "(无标题)"}
          </Link>
          {item.summary_zh && v !== "dim" && (
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-neutral-600 dark:text-neutral-400">
              {item.summary_zh}
            </p>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-neutral-500">
            <span>{item.source_name || item.source_type}</span>
            {item.author && (
              <>
                <span>·</span>
                <Link onClick={(e) => e.stopPropagation()} href={`/author/${slugify(item.author)}`} className="hover:text-neutral-900 hover:underline dark:hover:text-neutral-100">
                  {item.author}
                </Link>
              </>
            )}
            {(item.published_at || item.ingested_at) && <span>· {(item.published_at || item.ingested_at).slice(0, 10)}</span>}
            <span>· 📖 {estimateMinutes(bodyText)} 分钟</span>
            {(item.tags || []).slice(0, 4).map((t) => (
              <span key={t} className="rounded-full bg-blue-50 px-2 py-0.5 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300">#{t}</span>
            ))}
          </div>
          <div className="mt-3 min-h-5"><ScoreBreakdownChip breakdown={item.score_breakdown} score={item.final_score} /></div>
        </div>
        {(onKeep || onArchive || onTrash) && (
          <div className="flex shrink-0 gap-1">
            {onKeep && <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); onKeep(); }} className="rounded-lg bg-green-100 px-2 py-1 text-xs text-green-800 hover:bg-green-200 dark:bg-green-900/40 dark:text-green-200">保留</button>}
            {onArchive && <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); onArchive(); }} className="rounded-lg bg-neutral-100 px-2 py-1 text-xs hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700">归档</button>}
            {onTrash && <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); onTrash(); }} className="rounded-lg bg-red-100 px-2 py-1 text-xs text-red-800 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-200">删除</button>}
          </div>
        )}
      </div>
    </article>
  );
}
