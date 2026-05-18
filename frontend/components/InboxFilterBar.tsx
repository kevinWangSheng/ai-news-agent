"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { useTopics } from "@/lib/api/hooks";
import type { SourceTier } from "@/lib/tier";

const tiers: { value: SourceTier | ""; label: string }[] = [
  { value: "", label: "全部来源" },
  { value: "official", label: "🏛️ 官方" },
  { value: "expert", label: "✍️ 专家" },
  { value: "github", label: "💻 GitHub" },
  { value: "twitter", label: "🐦 Twitter" },
  { value: "aggregator", label: "📰 聚合" },
  { value: "chinese", label: "🇨🇳 中文" },
  { value: "manual", label: "✋ 手动" },
];

export function readInboxFilters(searchParams: URLSearchParams) {
  return {
    since: searchParams.get("since") || "all",
    tier: searchParams.get("tier") || "",
    topic: searchParams.get("topic") || "",
    min_score: searchParams.get("min_score") || "",
    status: searchParams.get("status") || "inbox",
    sort: searchParams.get("sort") || "score",
  };
}

export function InboxFilterBar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const filters = readInboxFilters(searchParams);
  const { data: topics } = useTopics();

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams.toString());
    if (!value || value === "all" && key !== "since") next.delete(key);
    else next.set(key, value);
    if (key !== "sort" && !next.get("sort")) next.set("sort", "score");
    router.replace(`/inbox?${next.toString()}`, { scroll: false });
  }

  const selectClass = "rounded-lg border border-neutral-200 bg-white px-3 py-2 text-xs outline-none hover:border-neutral-300 dark:border-neutral-800 dark:bg-neutral-950";

  return (
    <div className="sticky top-0 z-20 -mx-1 mb-4 rounded-2xl border border-neutral-200/70 bg-white/90 p-3 shadow-sm backdrop-blur dark:border-neutral-800/70 dark:bg-neutral-950/85">
      <div className="flex flex-wrap items-center gap-2">
        <select className={selectClass} value={filters.since} onChange={(e) => setFilter("since", e.target.value)}>
          <option value="all">全部时间</option>
          <option value="24h">24h 内</option>
          <option value="7d">7 天内</option>
        </select>
        <select className={selectClass} value={filters.tier} onChange={(e) => setFilter("tier", e.target.value)}>
          {tiers.map((tier) => <option key={tier.value || "all"} value={tier.value}>{tier.label}</option>)}
        </select>
        <select className={selectClass} value={filters.topic} onChange={(e) => setFilter("topic", e.target.value)}>
          <option value="">全部主题</option>
          {(topics || []).map((t) => <option key={t.slug} value={t.slug}>{t.name_zh || t.slug}</option>)}
        </select>
        <select className={selectClass} value={filters.min_score} onChange={(e) => setFilter("min_score", e.target.value)}>
          <option value="">不限分</option>
          <option value="6">≥ 6</option>
          <option value="7">≥ 7</option>
          <option value="8">≥ 8</option>
          <option value="9">≥ 9</option>
        </select>
        <select className={selectClass} value={filters.status} onChange={(e) => setFilter("status", e.target.value)}>
          <option value="inbox">Inbox</option>
          <option value="kept">Kept</option>
          <option value="archived">Archived</option>
          <option value="trashed">Trashed</option>
          <option value="all">全部状态</option>
        </select>
        <select className={selectClass} value={filters.sort} onChange={(e) => setFilter("sort", e.target.value)}>
          <option value="score">按分数</option>
          <option value="time">按时间</option>
        </select>
      </div>
    </div>
  );
}
