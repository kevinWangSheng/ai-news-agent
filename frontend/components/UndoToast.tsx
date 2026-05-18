"use client";
import { toast } from "sonner";

export function showUndoToast(message: string, onUndo: () => void) {
  return toast(message, {
    duration: 5000,
    action: { label: "撤销", onClick: onUndo },
  });
}
