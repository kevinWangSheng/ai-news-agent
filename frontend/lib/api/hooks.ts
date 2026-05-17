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

export function useItems(params: { status?: string; source_name?: string; topic?: string; limit?: number; cursor?: string }) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== "") as [string, string][]
  ).toString();
  return useSWR<Page<Item>>(`/api/items?${qs}`);
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

export async function patchItem(id: number, body: Partial<Pick<Item, "status" | "user_note" | "tags">>) {
  const res = await apiFetch<Item>(`/api/items/${id}`, { method: "PATCH", body: JSON.stringify(body) });
  mutate(`/api/items/${id}`);
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
