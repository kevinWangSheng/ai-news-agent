"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Inbox,
  Library,
  Hash,
  Users,
  Newspaper,
  Settings,
  Radio,
} from "lucide-react";
import clsx from "clsx";

const nav = [
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/library", label: "Library", icon: Library },
  { href: "/topics", label: "主题", icon: Hash },
  { href: "/entities", label: "实体", icon: Users },
  { href: "/digest", label: "精选", icon: Newspaper },
  { href: "/sources", label: "信源", icon: Radio },
  { href: "/settings", label: "设置", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 border-r border-neutral-200/60 dark:border-neutral-800/60 hidden md:flex flex-col">
      <div className="px-5 py-5 text-lg font-semibold">ai-agent-hub</div>
      <nav className="px-2 flex-1">
        {nav.map((n) => {
          const Icon = n.icon;
          const active = pathname?.startsWith(n.href);
          return (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800",
                active && "bg-neutral-100 dark:bg-neutral-800 font-medium"
              )}
            >
              <Icon className="size-4" />
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-3 text-xs text-neutral-500">v0.1.0 dev</div>
    </aside>
  );
}
