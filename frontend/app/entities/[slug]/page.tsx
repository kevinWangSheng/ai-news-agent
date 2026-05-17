"use client";
import { use } from "react";
import useSWR from "swr";
import type { Entity, Item } from "@/lib/api/hooks";
import { ItemCard } from "@/components/ItemCard";

export default function EntityDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { data: entity } = useSWR<Entity>(`/api/entities/${slug}`);
  const { data: items } = useSWR<Item[]>(`/api/entities/${slug}/items?limit=100`);
  return (
    <section>
      <h1 className="text-2xl font-semibold">{entity?.name ?? slug}</h1>
      <p className="text-sm text-neutral-500 mb-4">
        {entity?.type ?? "?"} · {entity?.item_count ?? items?.length ?? 0} 条相关
      </p>
      <div className="space-y-3">
        {(items ?? []).map((it) => <ItemCard key={it.id} item={it} />)}
      </div>
    </section>
  );
}
