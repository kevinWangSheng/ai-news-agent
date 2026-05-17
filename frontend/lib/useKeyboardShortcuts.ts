"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function useKeyboardShortcuts() {
  const router = useRouter();
  useEffect(() => {
    let last = "";
    let timer: ReturnType<typeof setTimeout> | null = null;

    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;
      const k = e.key.toLowerCase();
      if (last === "g") {
        if (k === "i") router.push("/inbox");
        else if (k === "l") router.push("/library");
        else if (k === "t") router.push("/topics");
        else if (k === "e") router.push("/entities");
        else if (k === "d") router.push("/digest");
        last = "";
        return;
      }
      if (k === "g") {
        last = "g";
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => (last = ""), 800);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [router]);
}
