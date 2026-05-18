"""Ranking helpers for score priors and diversified top lists.

The raw LLM quality score is item-level relevance. Ranking adds editorial priors
and list-level diversity so a high-volume source type cannot occupy the entire
homepage during cold start.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Literal

SourceTier = Literal["official", "expert", "aggregator", "github", "manual", "other"]

OFFICIAL_BLOGS = {
    "OpenAI Blog",
    "Anthropic News",
    "Claude Blog",
    "Google AI Blog",
    "Google DeepMind",
    "Meta AI Blog",
    "xAI News",
    "Mistral News",
    "Qwen Blog",
    "Cohere Blog",
    "HuggingFace Blog",
    "LangChain Blog",
    "LlamaIndex Blog",
    "AutoGen / AG2",
    "Thinking Machines Lab",
    "Cognition (Devin)",
    "Cursor",
    "Reka",
    "Liquid AI",
    "Sierra",
    "Glean",
    "Magic.dev",
    "Browserbase",
    "World Labs",
    "AMI Labs (LeCun)",
    "Manus",
    "Genspark",
}

EXPERT_BLOGS = {
    "Simon Willison's Weblog",
    "Sebastian Raschka",
    "Andrej Karpathy",
    "Lilian Weng",
    "Eugene Yan",
    "Chip Huyen",
    "Hamel Husain",
    "Philipp Schmid",
    "Latent Space (swyx)",
}

AGGREGATORS = {
    "The Batch (DeepLearning.AI)",
    "Import AI (Jack Clark)",
    "AINews (smol.ai)",
    "Latent Space Newsletter",
    "arXiv AI",
    "arXiv Multi-Agent Systems",
}


def source_tier(source_type: str | None, source_name: str | None) -> SourceTier:
    if source_type == "github":
        return "github"
    if source_type == "manual":
        return "manual"
    if source_name in OFFICIAL_BLOGS:
        return "official"
    if source_name in EXPERT_BLOGS:
        return "expert"
    if source_name in AGGREGATORS:
        return "aggregator"
    return "other"


def source_prior(source_type: str | None, source_name: str | None) -> float:
    """Cold-start editorial prior by source credibility / feed role.

    This deliberately bypasses preference cold-start. User interactions should
    still learn personal preference, but source priors prevent GitHub volume from
    drowning official/expert material before enough feedback exists.
    """
    tier = source_tier(source_type, source_name)
    if tier == "official":
        return 0.45
    if tier == "expert":
        return 0.25
    if tier == "aggregator":
        return 0.10
    if tier == "github":
        return -0.45
    if tier == "manual":
        return 0.10
    return 0.0


def resolve_tier(tier: str) -> tuple[str, set[str]] | None:
    if tier in {"github", "twitter", "chinese", "manual"}:
        return "source_type", {tier}
    if tier == "official":
        return "source_name", OFFICIAL_BLOGS
    if tier == "expert":
        return "source_name", EXPERT_BLOGS
    if tier == "aggregator":
        return "source_name", AGGREGATORS
    return None


def diversify_ranked_items(
    items: Iterable,
    limit: int,
    *,
    type_caps: dict[str, int] | None = None,
    source_cap: int | None = None,
    backfill: bool = True,
) -> list:
    """Apply simple source diversity caps to an already score-sorted candidate list.

    The caps are intentionally soft at the candidate-pool level: once all eligible
    diverse items are exhausted, we backfill from skipped items so the API still
    returns `limit` rows.
    """
    rows = list(items)
    if limit <= 0 or not rows:
        return []

    type_caps = type_caps if type_caps is not None else {
        "github": max(3, int(limit * 0.36)),
        "rss": max(6, int(limit * 0.50)),
        "web": max(6, int(limit * 0.50)),
    }
    source_cap = source_cap if source_cap is not None else max(2, int(limit * 0.06))
    selected = []
    skipped = []
    type_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()

    for item in rows:
        source_type = item.source_type or ""
        source_name = item.source_name or ""
        if source_type in type_caps and type_counts[source_type] >= type_caps[source_type]:
            skipped.append(item)
            continue
        if source_counts[source_name] >= source_cap:
            skipped.append(item)
            continue
        selected.append(item)
        type_counts[source_type] += 1
        source_counts[source_name] += 1
        if len(selected) >= limit:
            return selected

    if backfill:
        for item in skipped:
            if item in selected:
                continue
            selected.append(item)
            if len(selected) >= limit:
                break
    return selected
