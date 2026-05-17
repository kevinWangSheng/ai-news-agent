"""Exa-driven search — merges legacy breaking_news_agent + ai_content_agent.

Drives by site_queries + keyword_queries from topics.yaml (003 Task 10).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from app.ingestion.base import RawItem

EXA_URL = "https://api.exa.ai/search"


class ExaSearchSource:
    source_type = "exa_search"
    name = "exa_search"

    def __init__(
        self,
        site_queries: list[dict],
        keyword_queries: list[str],
        days_window: int = 3,
        per_query: int = 8,
    ) -> None:
        self.site_queries = site_queries
        self.keyword_queries = keyword_queries
        self.days_window = days_window
        self.per_query = per_query

    async def fetch(self) -> list[RawItem]:
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            return []

        since = (datetime.now(timezone.utc) - timedelta(days=self.days_window)).isoformat()
        out: list[RawItem] = []
        async with httpx.AsyncClient(
            headers={"x-api-key": api_key, "Content-Type": "application/json"}, timeout=30
        ) as client:
            for sq in self.site_queries:
                out += await self._search(
                    client, sq.get("query", ""), since, include_domains=[sq["site"]]
                )
            for kw in self.keyword_queries:
                out += await self._search(client, kw, since)
        return out

    async def _search(
        self,
        client: httpx.AsyncClient,
        query: str,
        since: str,
        include_domains: list[str] | None = None,
    ) -> list[RawItem]:
        payload: dict = {
            "query": query,
            "numResults": self.per_query,
            "startPublishedDate": since,
            "type": "auto",
        }
        if include_domains:
            payload["includeDomains"] = include_domains
        try:
            r = await client.post(EXA_URL, json=payload)
            r.raise_for_status()
        except httpx.HTTPError:
            return []
        items = []
        for res in r.json().get("results", []):
            items.append(
                RawItem(
                    url=res.get("url"),
                    title=res.get("title"),
                    source_type=self.source_type,
                    source_name=f"exa:{include_domains[0] if include_domains else 'keyword'}",
                    author=res.get("author"),
                    published_at=_parse(res.get("publishedDate")),
                    source_meta={"score": res.get("score"), "query": query},
                )
            )
        return items


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
