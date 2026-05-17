"""RSS / web source — replaces legacy tech_agent.py.

Reads `tech_sources.official_blogs / expert_blogs / aggregator_sources / research_sources`
from backend/config.yaml (003 Task 10 will move it here).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from app.ingestion.base import RawItem


class RssSource:
    source_type = "rss"

    def __init__(self, name: str, urls: list[str], max_items: int = 15) -> None:
        self.name = name
        self.urls = urls
        self.max_items = max_items

    async def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        async with httpx.AsyncClient(
            headers={"User-Agent": "ai-agent-hub/0.1"}, timeout=20, follow_redirects=True
        ) as client:
            for url in self.urls:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                except httpx.HTTPError:
                    continue
                parsed = await asyncio.to_thread(feedparser.parse, r.content)
                for entry in parsed.entries[: self.max_items]:
                    items.append(self._to_raw(entry))
                if items:
                    break  # primary worked; skip fallbacks
        return items

    def _to_raw(self, entry: Any) -> RawItem:
        published = None
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return RawItem(
            url=entry.get("link"),
            title=entry.get("title"),
            source_type=self.source_type,
            source_name=self.name,
            author=entry.get("author"),
            published_at=published,
            source_meta={"raw_summary": entry.get("summary", "")[:500]},
        )


def build_rss_sources(cfg: dict) -> list[RssSource]:
    """Build sources from a config dict shaped like config.yaml's tech_sources."""
    sources: list[RssSource] = []
    tech = cfg.get("tech_sources", {})
    for bucket_name in ("official_blogs", "expert_blogs", "aggregator_sources", "research_sources"):
        for entry in tech.get(bucket_name, []) or []:
            urls = [entry["url"]] if entry.get("url") else []
            urls += entry.get("fallback_urls", []) or []
            sources.append(
                RssSource(
                    name=entry["name"],
                    urls=urls,
                    max_items=int(entry.get("max_items", 15)),
                )
            )
    return sources
