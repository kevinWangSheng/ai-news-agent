"use client";

import { SWRConfig } from "swr";
import { ThemeProvider } from "next-themes";
import { CommandPalette } from "@/components/CommandPalette";
import { useKeyboardShortcuts } from "@/lib/useKeyboardShortcuts";
import { apiFetch } from "@/lib/api/client";
import { Toaster } from "sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  useKeyboardShortcuts();
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <SWRConfig value={{ fetcher: apiFetch, revalidateOnFocus: false }}>
        {children}
        <CommandPalette />
        <Toaster richColors closeButton position="bottom-right" />
      </SWRConfig>
    </ThemeProvider>
  );
}
