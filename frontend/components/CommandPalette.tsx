"use client";
import { Command } from "cmdk";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="命令面板"
      className="fixed inset-0 z-50 flex items-start justify-center pt-32 bg-black/30"
    >
      <div className="bg-white dark:bg-neutral-900 rounded-lg shadow-xl w-full max-w-lg overflow-hidden border border-neutral-200 dark:border-neutral-800">
        <Command.Input placeholder="输入命令..." className="w-full px-4 py-3 outline-none bg-transparent" />
        <Command.List className="max-h-80 overflow-y-auto p-2">
          <Command.Empty className="px-3 py-2 text-sm text-neutral-500">无匹配</Command.Empty>
          <Command.Group heading="导航">
            <Item label="去 Inbox" onSelect={() => { setOpen(false); router.push("/inbox"); }} />
            <Item label="去 Library" onSelect={() => { setOpen(false); router.push("/library"); }} />
            <Item label="去 主题" onSelect={() => { setOpen(false); router.push("/topics"); }} />
            <Item label="去 实体" onSelect={() => { setOpen(false); router.push("/entities"); }} />
            <Item label="去 精选" onSelect={() => { setOpen(false); router.push("/digest"); }} />
            <Item label="去 信源" onSelect={() => { setOpen(false); router.push("/sources"); }} />
            <Item label="去 设置" onSelect={() => { setOpen(false); router.push("/settings"); }} />
          </Command.Group>
          <Command.Group heading="操作">
            <Item label="切换主题" onSelect={() => setTheme(theme === "dark" ? "light" : "dark")} />
            <Item label="刷新当前页" onSelect={() => location.reload()} />
          </Command.Group>
        </Command.List>
      </div>
    </Command.Dialog>
  );
}

function Item({ label, onSelect }: { label: string; onSelect: () => void }) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="px-3 py-2 rounded text-sm cursor-pointer data-[selected=true]:bg-neutral-100 dark:data-[selected=true]:bg-neutral-800"
    >
      {label}
    </Command.Item>
  );
}
