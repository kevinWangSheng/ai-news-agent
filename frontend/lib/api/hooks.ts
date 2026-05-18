"use client";
import useSWR, { mutate } from "swr";
import { apiFetch } from "./client";

export type Item = {
  id: number;
  url: string | null;
  title: string | null;
  title_cn: string | null;
  summary_zh: string | null;
  summary_en: string | null;
  recommendation: string | null;
  source_type: string;
  source_name: string | null;
  author: string | null;
  published_at: string | null;
  ingested_at: string;
  status: string;
  processing_status: string;
  quality_score: number | null;
  final_score: number | null;
  tags: string[] | null;
  user_note: string | null;
  viewed_at?: string | null;
  score_breakdown?: Record<string, unknown> | null;
};

export type ItemDetail = Item & {
  content_md: string | null;
  score_breakdown: Record<string, unknown> | null;
  topics: Topic[];
  entities: Entity[];
  related_items: Item[];
};

export type Topic = {
  id: number;
  slug: string;
  name_zh: string;
  name_en?: string | null;
  description?: string | null;
  is_pinned: boolean;
  item_count: number;
  last_item_at?: string | null;
};

export type Entity = {
  id: number;
  slug: string;
  type: string;
  name: string;
  item_count: number;
  last_item_at?: string | null;
};

export type Page<T> = { items: T[]; next_cursor: string | null };
export type ItemLanes = { top_signals: Item[]; official_updates: Item[]; repo_radar: Item[] };
export type ItemFilters = {
  status?: string;
  source_name?: string;
  source_type?: string;
  topic?: string;
  entity?: string;
  since?: "24h" | "7d" | "all" | string;
  tier?: string;
  min_score?: number | string;
  sort?: "score" | "time" | string;
  limit?: number;
  cursor?: string;
};

function qs(params: Record<string, unknown>) {
  return new URLSearchParams(
    Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => [k, String(v)])
  ).toString();
}

export function useItems(params: ItemFilters | null) {
  if (params === null) return useSWR<Page<Item>>(null);
  const query = qs(params);
  return useSWR<Page<Item>>(`/api/items?${query}`);
}

export function useItemLanes(params: Pick<ItemFilters, "status" | "since" | "limit"> | null = {}) {
  if (params === null) return useSWR<ItemLanes>(null);
  const query = qs(params);
  return useSWR<ItemLanes>(`/api/items/lanes?${query}`);
}

export function useItem(id: number | null) {
  return useSWR<ItemDetail>(id ? `/api/items/${id}` : null);
}

export function useSearch(q: string, mode: "hybrid" | "fulltext" | "semantic" = "hybrid") {
  return useSWR<{ total: number; items: Item[]; facets: Record<string, { value: string; count: number }[]> }>(
    q ? `/api/search?q=${encodeURIComponent(q)}&mode=${mode}` : null
  );
}

export function useTopics() {
  return useSWR<Topic[]>("/api/topics");
}

export function useEntities(type?: string) {
  return useSWR<Entity[]>(`/api/entities${type ? `?type=${type}` : ""}`);
}

export function useDigests(period?: "daily" | "weekly" | "topic") {
  return useSWR(`/api/digests${period ? `?period=${period}` : ""}`);
}

export function useSources() {
  return useSWR("/api/sources");
}

export function useHealthScoring() {
  return useSWR<{ total_interactions: number; cold_start_passed: boolean; cold_start_min: number }>("/health/scoring");
}

export function useAuthors() {
  return useSWR<{ value: string; count: number }[]>("/api/authors");
}

export function useAuthorItems(slug: string | null) {
  return useSWR<Item[]>(slug ? `/api/authors/${slug}/items` : null);
}

export async function patchItem(id: number, body: Partial<Pick<Item, "status" | "user_note" | "tags">>) {
  mutate<ItemDetail | undefined>(
    `/api/items/${id}`,
    (current) => (current ? { ...current, ...body } : current),
    { revalidate: false }
  );
  const res = await apiFetch<Item>(`/api/items/${id}`, { method: "PATCH", body: JSON.stringify(body) });
  mutate(`/api/items/${id}`);
  mutate((key) => typeof key === "string" && key.startsWith("/api/items?"));
  return res;
}

export async function bulkPatchItems(ids: number[], action: "kept" | "archived" | "trashed") {
  const res = await apiFetch<{ updated: number }>("/api/items/bulk", {
    method: "POST",
    body: JSON.stringify({ ids, action }),
  });
  mutate((key) => typeof key === "string" && key.startsWith("/api/items?"));
  return res;
}

export async function recordInteraction(
  id: number,
  action: "view" | "keep" | "archive" | "trash" | "highlight" | "note" | "share",
  extra: { dwell_seconds?: number; note_text?: string; highlight_text?: string } = {}
) {
  return apiFetch<{ id: number }>(`/api/items/${id}/interactions`, {
    method: "POST",
    body: JSON.stringify({ action, ...extra }),
  });
}
