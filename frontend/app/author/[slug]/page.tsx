"use client";
import { use } from "react";
import { useAuthorItems } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

export default function AuthorPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { data, isLoading, error } = useAuthorItems(slug);
  const author = data?.[0]?.author || decodeURIComponent(slug);
  return (
    <section>
      <header className="mb-5">
        <h1 className="text-2xl font-semibold">{author}</h1>
        <p className="mt-1 text-sm text-neutral-500">作者历史条目 {data?.length ?? 0} 条</p>
      </header>
      {isLoading && <div className="h-32 animate-pulse rounded-2xl bg-neutral-100 dark:bg-neutral-900" />}
      {error && <p className="text-sm text-red-500">{String(error)}</p>}
      <div className="space-y-3">{(data || []).map((item) => <ItemCard key={item.id} item={item} />)}</div>
    </section>
  );
}
