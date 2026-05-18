import { estimateMinutes } from "@/lib/readingTime";

export function ReadingTimeBadge({ content }: { content: string | null | undefined }) {
  return <span className="inline-flex items-center gap-1 text-xs text-neutral-500">📖 {estimateMinutes(content)} 分钟</span>;
}
