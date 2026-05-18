import { getSourceTier, TIER_META } from "@/lib/tier";

export function TierBadge({ item, compact = false }: { item: { source_type: string; source_name: string | null }; compact?: boolean }) {
  const tier = getSourceTier(item);
  const meta = TIER_META[tier];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${meta.bgClass}`} title={meta.label}>
      <span>{meta.emoji}</span>
      {!compact && <span>{meta.label}</span>}
    </span>
  );
}
