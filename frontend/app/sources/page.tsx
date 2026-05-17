"use client";
import { useSources } from "@/lib/api/hooks";
import { apiFetch } from "@/lib/api/client";
import { mutate } from "swr";

type Source = {
  name: string;
  source_type: string;
  last_run_at: string | null;
  last_success_at: string | null;
  error_count: number;
  next_run_at: string | null;
};

export default function SourcesPage() {
  const { data, isLoading } = useSources() as { data: Source[] | undefined; isLoading: boolean };
  return (
    <section>
      <h1 className="text-2xl font-semibold mb-4">信源</h1>
      {isLoading && <p className="text-sm text-neutral-500">加载中…</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-neutral-500">
            <tr>
              <th className="py-2">name</th>
              <th>type</th>
              <th>last_success</th>
              <th>errors(7d)</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((s) => (
              <tr key={s.name + s.source_type} className="border-t border-neutral-200 dark:border-neutral-800">
                <td className="py-2">{s.name}</td>
                <td>{s.source_type}</td>
                <td>{s.last_success_at?.slice(0, 19) ?? "—"}</td>
                <td>{s.error_count}</td>
                <td>
                  <button
                    onClick={async () => { await apiFetch(`/api/sources/${encodeURIComponent(s.name)}/trigger`, { method: "POST" }); mutate("/api/sources"); }}
                    className="text-xs px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/40"
                  >
                    触发
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
