export type SourceTier = "official" | "expert" | "github" | "twitter" | "aggregator" | "chinese" | "manual";

export const TIER_META: Record<SourceTier, { emoji: string; label: string; color: string; bgClass: string }> = {
  official: { emoji: "🏛️", label: "官方", color: "#7c3aed", bgClass: "bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300" },
  expert: { emoji: "✍️", label: "专家", color: "#0891b2", bgClass: "bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300" },
  github: { emoji: "💻", label: "GitHub", color: "#374151", bgClass: "bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300" },
  twitter: { emoji: "🐦", label: "Tweet", color: "#1d9bf0", bgClass: "bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300" },
  aggregator: { emoji: "📰", label: "聚合", color: "#ea580c", bgClass: "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300" },
  chinese: { emoji: "🇨🇳", label: "中文", color: "#dc2626", bgClass: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300" },
  manual: { emoji: "✋", label: "手动", color: "#6b7280", bgClass: "bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300" },
};

export const OFFICIAL_BLOGS = new Set([
  "OpenAI Blog", "Anthropic News", "Claude Blog", "Google AI Blog", "Google DeepMind",
  "Meta AI Blog", "xAI News", "Mistral News", "Qwen Blog", "Cohere Blog",
  "HuggingFace Blog", "LangChain Blog", "LlamaIndex Blog", "AutoGen / AG2",
  "Thinking Machines Lab", "Cognition (Devin)", "Cursor", "Reka", "Liquid AI",
  "Sierra", "Glean", "Magic.dev", "Browserbase", "World Labs", "AMI Labs (LeCun)",
  "Manus", "Genspark",
]);

export const EXPERT_BLOGS = new Set([
  "Simon Willison's Weblog", "Sebastian Raschka", "Andrej Karpathy", "Lilian Weng",
  "Eugene Yan", "Chip Huyen", "Hamel Husain", "Philipp Schmid", "Latent Space (swyx)",
]);

export const AGGREGATORS = new Set([
  "The Batch (DeepLearning.AI)", "Import AI (Jack Clark)", "AINews (smol.ai)",
  "Latent Space Newsletter", "arXiv AI", "arXiv Multi-Agent Systems",
]);

export function getSourceTier(item: { source_type: string; source_name: string | null }): SourceTier {
  if (item.source_type === "github") return "github";
  if (item.source_type === "twitter") return "twitter";
  if (item.source_type === "chinese") return "chinese";
  if (item.source_type === "manual") return "manual";
  const name = item.source_name || "";
  if (OFFICIAL_BLOGS.has(name)) return "official";
  if (EXPERT_BLOGS.has(name)) return "expert";
  if (AGGREGATORS.has(name)) return "aggregator";
  return "expert";
}
