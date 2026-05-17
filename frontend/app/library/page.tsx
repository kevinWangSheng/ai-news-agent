"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useItems, useSearch } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

function LibraryInner() {
  const sp = useSearchParams();
  const q = sp.get("q") ?? "";
  const [mode, setMode] = useState<"hybrid" | "fulltext" | "semantic">("hybrid");
  const [source, setSource] = useState<string>("");
  const [topic, setTopic] = useState<string>("");

  const searchRes = useSearch(q, mode);
  const listRes = useItems({ source_name: source, topic, limit: 50 });

  const items = q ? searchRes.data?.items ?? [] : listRes.data?.items ?? [];
  const total = q ? searchRes.data?.total ?? 0 : items.length;

  return (
    <section>
      <header className="mb-4 flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold">Library</h1>
        <span className="text-sm text-neutral-500">{total} 条</span>
      </header>
      <div className="flex gap-2 items-center text-sm mb-4 flex-wrap">
        {q ? (
          <>
            <span>查询:<code className="bg-neutral-100 dark:bg-neutral-800 px-1.5 py-0.5 rounded">{q}</code></span>
            <select value={mode} onChange={(e) => setMode(e.target.value as "hybrid" | "fulltext" | "semantic")} className="border rounded px-2 py-1 bg-transparent">
              <option value="hybrid">hybrid</option>
              <option value="fulltext">fulltext</option>
              <option value="semantic">semantic</option>
            </select>
          </>
        ) : (
          <>
            <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="source_name 过滤" className="border rounded px-2 py-1 bg-transparent" />
            <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="topic slug 过滤" className="border rounded px-2 py-1 bg-transparent" />
          </>
        )}
      </div>
      <div className="space-y-3">
        {items.map((it) => <ItemCard key={it.id} item={it} />)}
        {items.length === 0 && <p className="text-sm text-neutral-500">无结果</p>}
      </div>
    </section>
  );
}

export default function LibraryPage() {
  return (
    <Suspense fallback={<p className="text-sm text-neutral-500">加载中…</p>}>
      <LibraryInner />
    </Suspense>
  );
}
