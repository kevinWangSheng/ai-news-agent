"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Search, Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";

export function TopBar() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    const onSlash = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (e.key === "/" && target && target.tagName !== "INPUT" && target.tagName !== "TEXTAREA") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onSlash);
    return () => window.removeEventListener("keydown", onSlash);
  }, []);

  return (
    <div className="flex items-center justify-between border-b border-neutral-200/60 dark:border-neutral-800/60 px-6 py-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (q.trim()) router.push(`/library?q=${encodeURIComponent(q.trim())}`);
        }}
        className="flex items-center gap-2 flex-1 max-w-xl"
      >
        <Search className="size-4 text-neutral-500" />
        <input
          ref={inputRef}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="搜索 / 检索 (按 / 聚焦, Esc 失焦)"
          onKeyDown={(e) => e.key === "Escape" && (e.target as HTMLInputElement).blur()}
          className="flex-1 bg-transparent outline-none text-sm placeholder:text-neutral-400"
        />
      </form>
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-500 hidden sm:inline">⌘K 唤起命令面板</span>
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-2 rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800"
          aria-label="toggle theme"
        >
          <Sun className="size-4 dark:hidden" />
          <Moon className="size-4 hidden dark:inline" />
        </button>
      </div>
    </div>
  );
}
