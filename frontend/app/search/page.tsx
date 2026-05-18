"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useSearch } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

export default function SearchPage() {
  return <Suspense fallback={<p className="text-sm text-neutral-500">搜索中…</p>}><SearchInner /></Suspense>;
}

function SearchInner() {
  const params = useSearchParams();
  const q = params.get("q") || "";
  const { data, isLoading, error } = useSearch(q);
  return (
    <section>
      <header className="mb-5">
        <h1 className="text-2xl font-semibold">Search</h1>
        <p className="mt-1 text-sm text-neutral-500">{q ? `“${q}” 的结果` : "在顶栏输入关键词开始搜索"}</p>
      </header>
      {isLoading && <div className="h-32 animate-pulse rounded-2xl bg-neutral-100 dark:bg-neutral-900" />}
      {error && <p className="text-sm text-red-500">{String(error)}</p>}
      <div className="space-y-3">
        {(data?.items || []).map((item) => <ItemCard key={item.id} item={item} />)}
        {q && data && data.items.length === 0 && <p className="text-sm text-neutral-500">没有找到结果。</p>}
      </div>
    </section>
  );
}
