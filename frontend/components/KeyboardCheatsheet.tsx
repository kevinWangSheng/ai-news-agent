"use client";

const rows = [
  ["j / k", "上下移动焦点"], ["o / Enter", "打开详情"], ["s", "Keep"], ["e", "Archive"], ["x", "Delete"], ["/", "聚焦搜索"], ["g i", "Inbox"], ["g l", "Library"], ["g t", "Topics"], ["⌘Z", "撤销上一条延迟动作"],
];

export function KeyboardCheatsheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/35 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-2xl border border-neutral-200 bg-white p-5 shadow-2xl dark:border-neutral-800 dark:bg-neutral-950" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">键盘流</h2>
          <button onClick={onClose} className="rounded-full px-2 py-1 text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800">Esc</button>
        </div>
        <div className="mt-4 grid gap-2">
          {rows.map(([key, label]) => (
            <div key={key} className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2 text-sm dark:bg-neutral-900">
              <kbd className="font-mono text-xs text-neutral-500">{key}</kbd><span>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
