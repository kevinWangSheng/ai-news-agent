"use client";
export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="p-8">
      <h2 className="text-xl font-semibold">出错了</h2>
      <p className="mt-2 text-sm text-neutral-500">{error.message}</p>
      <button onClick={reset} className="mt-4 px-3 py-1.5 rounded bg-neutral-900 text-white text-sm">
        重试
      </button>
    </div>
  );
}
