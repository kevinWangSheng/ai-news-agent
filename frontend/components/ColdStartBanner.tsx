"use client";
import { useHealthScoring } from "@/lib/api/hooks";

export function ColdStartBanner() {
  const { data } = useHealthScoring();
  if (!data || data.cold_start_passed) return null;
  const pct = Math.min(100, Math.round((data.total_interactions / Math.max(1, data.cold_start_min)) * 100));
  return (
    <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-200">
      <div className="flex items-center justify-between gap-4">
        <strong>推荐还在冷启动</strong>
        <span className="font-mono text-xs">{data.total_interactions}/{data.cold_start_min}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-red-100 dark:bg-red-950">
        <div className="h-full rounded-full bg-red-500" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-xs">还没到 {data.cold_start_min} 次交互，推荐未完全启用；今晚先正常 keep/archive，系统会开始长出你的口味。</p>
    </div>
  );
}
