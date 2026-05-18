"use client";

export function BulkActionBar({ count, onKeep, onArchive, onDelete, onClear }: { count: number; onKeep: () => void; onArchive: () => void; onDelete: () => void; onClear: () => void }) {
  if (count < 2) return null;
  return (
    <div className="fixed bottom-5 left-1/2 z-40 flex -translate-x-1/2 items-center gap-2 rounded-full border border-neutral-200 bg-white/95 px-4 py-3 text-sm shadow-2xl backdrop-blur dark:border-neutral-800 dark:bg-neutral-950/95">
      <span className="mr-2 font-medium">{count} items selected</span>
      <button onClick={onKeep} className="rounded-full bg-green-100 px-3 py-1 text-green-800 hover:bg-green-200 dark:bg-green-900/40 dark:text-green-200">Keep all</button>
      <button onClick={onArchive} className="rounded-full bg-neutral-100 px-3 py-1 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700">Archive all</button>
      <button onClick={onDelete} className="rounded-full bg-red-100 px-3 py-1 text-red-800 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-200">Delete all</button>
      <button onClick={onClear} className="rounded-full px-3 py-1 text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800">Clear</button>
    </div>
  );
}
