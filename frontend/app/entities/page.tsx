"use client";
import { useState } from "react";
import Link from "next/link";
import { useEntities } from "@/lib/api/hooks";

const TYPES = ["", "person", "company", "project", "model", "paper"];

export default function EntitiesPage() {
  const [type, setType] = useState("");
  const { data, isLoading } = useEntities(type || undefined);
  return (
    <section>
      <header className="mb-4 flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold">实体</h1>
        <div className="flex gap-1 flex-wrap">
          {TYPES.map((t) => (
            <button
              key={t || "all"}
              onClick={() => setType(t)}
              className={`text-xs px-2 py-1 rounded ${type === t ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900" : "bg-neutral-100 dark:bg-neutral-800"}`}
            >
              {t || "全部"}
            </button>
          ))}
        </div>
      </header>
      {isLoading && <p className="text-sm text-neutral-500">加载中…</p>}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {(data ?? []).map((e) => (
          <Link
            key={e.slug}
            href={`/entities/${e.slug}`}
            className="rounded border border-neutral-200 dark:border-neutral-800 p-2 hover:bg-neutral-50 dark:hover:bg-neutral-900/40"
          >
            <div className="text-sm font-medium truncate">{e.name}</div>
            <div className="text-xs text-neutral-500">{e.type} · {e.item_count}</div>
          </Link>
        ))}
      </div>
    </section>
  );
}
