"use client";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { List } from "react-window";
import { useHotkeys } from "react-hotkeys-hook";
import { toast } from "sonner";
import { showUndoToast } from "@/components/UndoToast";
import { bulkPatchItems, type Item, recordInteraction, useItemLanes, useItems } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";
import { InboxFilterBar, readInboxFilters } from "@/components/InboxFilterBar";
import { ColdStartBanner } from "@/components/ColdStartBanner";
import { BulkActionBar } from "@/components/BulkActionBar";
import { KeyboardCheatsheet } from "@/components/KeyboardCheatsheet";
import { HOTKEYS } from "@/lib/hotkeys";

type Row = { type: "header"; id: string; label: string; count: number } | { type: "item"; id: string; item: Item };
type Pending = { id: number; timer: ReturnType<typeof setTimeout> };
type InboxRowData = { rows: Row[]; selected: Set<number>; focusedId: number | null; selectItem: (item: Item, shift: boolean, meta: boolean) => void; delayedAction: (item: Item, action: "keep" | "archive" | "trash") => void };

export default function InboxPage() {
  return <Suspense fallback={<SkeletonInbox />}><InboxInner /></Suspense>;
}

function InboxInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const filters = readInboxFilters(searchParams);
  const laneMode = isDefaultLaneMode(filters);
  const { data, error, isLoading, mutate } = useItems(laneMode ? null : { ...filters, limit: 300 });
  const { data: lanes, error: lanesError, isLoading: lanesLoading, mutate: mutateLanes } = useItemLanes(
    laneMode ? { status: filters.status, since: filters.since, limit: 20 } : null
  );
  const [hidden, setHidden] = useState<Set<number>>(new Set());
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [focusedId, setFocusedId] = useState<number | null>(null);
  const [lastSelected, setLastSelected] = useState<number | null>(null);
  const [cheatsheet, setCheatsheet] = useState(false);
  const pendingRef = useRef<Pending | null>(null);

  const laneGroups = useMemo(() => {
    if (!lanes) return [];
    return [
      {
        id: "top_signals",
        eyebrow: "Top Signals",
        title: "今日最值得先看",
        description: "跨源精选:官方、专家、GitHub 项目混合排序。",
        items: lanes.top_signals.filter((item) => !hidden.has(item.id)),
      },
      {
        id: "official_updates",
        eyebrow: "Official Updates",
        title: "官方与核心项目更新",
        description: "厂商、框架、模型团队的第一手动态。",
        items: lanes.official_updates.filter((item) => !hidden.has(item.id)),
      },
      {
        id: "repo_radar",
        eyebrow: "Repo Radar",
        title: "新工具与开源项目雷达",
        description: "GitHub 项目单独成栏,不再淹没官方情报。",
        items: lanes.repo_radar.filter((item) => !hidden.has(item.id)),
      },
    ];
  }, [hidden, lanes]);
  const laneItems = useMemo(() => {
    const byId = new Map<number, Item>();
    laneGroups.flatMap((lane) => lane.items).forEach((item) => byId.set(item.id, item));
    return [...byId.values()];
  }, [laneGroups]);
  const listItems = useMemo(() => (data?.items ?? []).filter((item) => !hidden.has(item.id)), [data?.items, hidden]);
  const visibleItems = laneMode ? laneItems : listItems;
  const itemIds = useMemo(() => visibleItems.map((item) => item.id), [visibleItems]);
  const rows = useMemo<Row[]>(() => {
    const now = Date.now();
    const today = visibleItems.filter((item) => now - new Date(item.ingested_at).getTime() <= 24 * 60 * 60 * 1000);
    const older = visibleItems.filter((item) => now - new Date(item.ingested_at).getTime() > 24 * 60 * 60 * 1000);
    const out: Row[] = [];
    if (today.length) out.push({ type: "header", id: "today", label: `今日新进 ${today.length} 条`, count: today.length }, ...today.map((item) => ({ type: "item" as const, id: `item-${item.id}`, item })));
    if (older.length) out.push({ type: "header", id: "older", label: "更早", count: older.length }, ...older.map((item) => ({ type: "item" as const, id: `item-${item.id}`, item })));
    return out;
  }, [visibleItems]);

  useEffect(() => {
    if (focusedId == null && itemIds.length) setFocusedId(itemIds[0]);
    if (focusedId != null && itemIds.length && !itemIds.includes(focusedId)) setFocusedId(itemIds[0]);
  }, [focusedId, itemIds]);

  function focusBy(delta: number) {
    if (!itemIds.length) return;
    const idx = Math.max(0, itemIds.indexOf(focusedId ?? itemIds[0]));
    const next = itemIds[(idx + delta + itemIds.length) % itemIds.length];
    setFocusedId(next);
    document.getElementById(`item-row-${next}`)?.scrollIntoView({ block: "nearest" });
  }

  function undoLast() {
    const pending = pendingRef.current;
    if (!pending) return;
    clearTimeout(pending.timer);
    setHidden((prev) => {
      const next = new Set(prev);
      next.delete(pending.id);
      return next;
    });
    pendingRef.current = null;
    toast.success("已撤销");
  }

  function delayedAction(item: Item, action: "keep" | "archive" | "trash") {
    const label = action === "keep" ? "已保留" : action === "archive" ? "已归档" : "已删除";
    setHidden((prev) => new Set(prev).add(item.id));
    setSelected((prev) => {
      const next = new Set(prev);
      next.delete(item.id);
      return next;
    });
    const timer = setTimeout(async () => {
      await recordInteraction(item.id, action).catch(() => {});
      pendingRef.current = null;
      if (laneMode) mutateLanes();
      else mutate();
    }, 5000);
    pendingRef.current = { id: item.id, timer };
    showUndoToast(label, undoLast);
  }

  function selectItem(item: Item, shift: boolean, meta: boolean) {
    setSelected((prev) => {
      const next = new Set(meta || shift ? prev : []);
      if (shift && lastSelected != null) {
        const a = itemIds.indexOf(lastSelected);
        const b = itemIds.indexOf(item.id);
        if (a >= 0 && b >= 0) itemIds.slice(Math.min(a, b), Math.max(a, b) + 1).forEach((id) => next.add(id));
      } else if (next.has(item.id)) next.delete(item.id);
      else next.add(item.id);
      return next;
    });
    setLastSelected(item.id);
    setFocusedId(item.id);
  }

  async function bulk(action: "kept" | "archived" | "trashed") {
    const ids = [...selected];
    if (!ids.length) return;
    setHidden((prev) => new Set([...prev, ...ids]));
    setSelected(new Set());
    await bulkPatchItems(ids, action);
    toast.success(`${ids.length} 条已${action === "kept" ? "保留" : action === "archived" ? "归档" : "删除"}`);
    if (laneMode) mutateLanes();
    else mutate();
  }

  useHotkeys(HOTKEYS.next, () => focusBy(1), { preventDefault: true }, [itemIds, focusedId]);
  useHotkeys(HOTKEYS.prev, () => focusBy(-1), { preventDefault: true }, [itemIds, focusedId]);
  useHotkeys(HOTKEYS.open, () => focusedId && router.push(`/item/${focusedId}`), { preventDefault: true }, [focusedId]);
  useHotkeys(HOTKEYS.keep, () => { const item = visibleItems.find((x) => x.id === focusedId); if (item) delayedAction(item, "keep"); }, { preventDefault: true }, [visibleItems, focusedId]);
  useHotkeys(HOTKEYS.archive, () => { const item = visibleItems.find((x) => x.id === focusedId); if (item) delayedAction(item, "archive"); }, { preventDefault: true }, [visibleItems, focusedId]);
  useHotkeys(HOTKEYS.trash, () => { const item = visibleItems.find((x) => x.id === focusedId); if (item) delayedAction(item, "trash"); }, { preventDefault: true }, [visibleItems, focusedId]);
  useHotkeys(HOTKEYS.help, () => setCheatsheet(true), { preventDefault: true });
  useHotkeys(HOTKEYS.inbox, () => router.push("/inbox"), { preventDefault: true });
  useHotkeys(HOTKEYS.library, () => router.push("/library"), { preventDefault: true });
  useHotkeys(HOTKEYS.topics, () => router.push("/topics"), { preventDefault: true });
  useHotkeys(HOTKEYS.undo, undoLast, { preventDefault: true });

  if ((laneMode && lanesLoading) || (!laneMode && isLoading)) return <SkeletonInbox />;
  if (laneMode && lanesError) return <p className="text-sm text-red-500">{String(lanesError)}</p>;
  if (!laneMode && error) return <p className="text-sm text-red-500">{String(error)}</p>;

  return (
    <section>
      <header className="mb-4 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Inbox</h1>
          <p className="mt-1 text-xs text-neutral-500">j/k 导航，e 归档，s 保留，? 看快捷键</p>
        </div>
        <span className="text-sm text-neutral-500">{visibleItems.length} 条待处理</span>
      </header>
      <ColdStartBanner />
      <InboxFilterBar />
      {laneMode ? (
        laneGroups.length === 0 || laneGroups.every((lane) => lane.items.length === 0) ? <EmptyInbox /> : (
          <div className="space-y-5">
            {laneGroups.map((lane) => (
              <LaneSection
                key={lane.id}
                lane={lane}
                selected={selected}
                focusedId={focusedId}
                selectItem={selectItem}
                delayedAction={delayedAction}
              />
            ))}
          </div>
        )
      ) : rows.length === 0 ? <EmptyInbox /> : rows.length > 80 ? (
        <List<InboxRowData>
          rowCount={rows.length}
          rowHeight={(index) => rowHeight(rows[index])}
          rowComponent={InboxRow}
          rowProps={{ rows, selected, focusedId, selectItem, delayedAction }}
          className="rounded-2xl"
          style={{ height: "calc(100vh - 260px)", minHeight: 520 }}
          overscanCount={6}
        />
      ) : (
        <div className="space-y-3">
          {rows.map((row) => row.type === "header" ? <SectionHeader key={row.id} label={row.label} /> : (
            <div key={row.id} id={`item-row-${row.item.id}`}>
              <ItemCard item={row.item} selected={selected.has(row.item.id)} focused={focusedId === row.item.id} onSelect={(shift, meta) => selectItem(row.item, shift, meta)} onKeep={() => delayedAction(row.item, "keep")} onArchive={() => delayedAction(row.item, "archive")} onTrash={() => delayedAction(row.item, "trash")} />
            </div>
          ))}
        </div>
      )}
      <BulkActionBar count={selected.size} onKeep={() => bulk("kept")} onArchive={() => bulk("archived")} onDelete={() => bulk("trashed")} onClear={() => setSelected(new Set())} />
      <KeyboardCheatsheet open={cheatsheet} onClose={() => setCheatsheet(false)} />
    </section>
  );
}

function isDefaultLaneMode(filters: ReturnType<typeof readInboxFilters>) {
  return (
    (filters.status || "inbox") === "inbox" &&
    (filters.sort || "score") === "score" &&
    (filters.since || "all") === "all" &&
    !filters.tier &&
    !filters.topic &&
    !filters.min_score
  );
}

function LaneSection({
  lane,
  selected,
  focusedId,
  selectItem,
  delayedAction,
}: {
  lane: { id: string; eyebrow: string; title: string; description: string; items: Item[] };
  selected: Set<number>;
  focusedId: number | null;
  selectItem: (item: Item, shift: boolean, meta: boolean) => void;
  delayedAction: (item: Item, action: "keep" | "archive" | "trash") => void;
}) {
  if (!lane.items.length) return null;
  return (
    <section className="overflow-hidden rounded-[1.75rem] border border-neutral-200 bg-neutral-50/70 p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950/60">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-neutral-200/80 pb-3 dark:border-neutral-800">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-neutral-400">{lane.eyebrow}</p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">{lane.title}</h2>
          <p className="mt-1 text-xs text-neutral-500">{lane.description}</p>
        </div>
        <span className="rounded-full bg-white px-3 py-1 text-xs text-neutral-500 shadow-sm dark:bg-neutral-900">{lane.items.length} 条</span>
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        {lane.items.slice(0, 8).map((item, index) => (
          <div key={`${lane.id}-${item.id}`} id={`item-row-${item.id}`} className={index === 0 ? "lg:col-span-2" : ""}>
            <ItemCard
              item={item}
              variant={index === 0 ? "top" : undefined}
              selected={selected.has(item.id)}
              focused={focusedId === item.id}
              onSelect={(shift, meta) => selectItem(item, shift, meta)}
              onKeep={() => delayedAction(item, "keep")}
              onArchive={() => delayedAction(item, "archive")}
              onTrash={() => delayedAction(item, "trash")}
            />
          </div>
        ))}
      </div>
    </section>
  );
}

function rowHeight(row: Row) {
  if (row.type === "header") return 44;
  const score = row.item.final_score ?? 0;
  if (row.item.viewed_at || (score > 0 && score < 7)) return 132;
  if (score >= 10) return 210;
  if (score >= 9) return 188;
  return 176;
}

function InboxRow({ index, style, rows, selected, focusedId, selectItem, delayedAction }: { index: number; style: CSSProperties } & InboxRowData) {
  const row = rows[index];
  if (row.type === "header") return <div style={style}><SectionHeader label={row.label} /></div>;
  return (
    <div style={{ ...style, paddingBottom: 12 }} id={`item-row-${row.item.id}`}>
      <ItemCard item={row.item} selected={selected.has(row.item.id)} focused={focusedId === row.item.id} onSelect={(shift, meta) => selectItem(row.item, shift, meta)} onKeep={() => delayedAction(row.item, "keep")} onArchive={() => delayedAction(row.item, "archive")} onTrash={() => delayedAction(row.item, "trash")} />
    </div>
  );
}

function SectionHeader({ label }: { label: string }) {
  return <h2 className="pt-2 text-xs font-semibold uppercase tracking-[0.18em] text-neutral-400">{label}</h2>;
}

function SkeletonInbox() {
  return <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-32 animate-pulse rounded-2xl bg-neutral-100 dark:bg-neutral-900" />)}</div>;
}

function EmptyInbox() {
  return <div className="rounded-2xl border border-dashed border-neutral-300 p-8 text-center text-neutral-500 dark:border-neutral-800">📭 今日已清空 — 下一批会自动跑进来。</div>;
}
