"""Twitter via Exa — replaces legacy twitter_agent.py."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from app.ingestion.base import RawItem

EXA_URL = "https://api.exa.ai/search"


class TwitterSource:
    source_type = "twitter"
    name = "twitter"

    def __init__(
        self,
        kol_accounts: list[str],
        official_accounts: list[str],
        topic_queries: list[str],
        days_window: int = 3,
    ) -> None:
        self.kol_accounts = kol_accounts
        self.official_accounts = official_accounts
        self.topic_queries = topic_queries
        self.days_window = days_window

    async def fetch(self) -> list[RawItem]:
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            return []

        since = (datetime.now(timezone.utc) - timedelta(days=self.days_window)).isoformat()
        out: list[RawItem] = []
        async with httpx.AsyncClient(
            headers={"x-api-key": api_key, "Content-Type": "application/json"}, timeout=30
        ) as client:
            for handle in self.kol_accounts + self.official_accounts:
                out += await self._search(
                    client,
                    query=f"recent tweets",
                    since=since,
                    include_domains=[f"x.com/{handle}", f"twitter.com/{handle}"],
                    source_name=f"twitter:{handle}",
                )
            for q in self.topic_queries:
                out += await self._search(
                    client,
                    query=q,
                    since=since,
                    include_domains=["x.com", "twitter.com"],
                    source_name=f"twitter:topic",
                )
        return out

    async def _search(
        self,
        client: httpx.AsyncClient,
        query: str,
        since: str,
        include_domains: list[str],
        source_name: str,
    ) -> list[RawItem]:
        try:
            r = await client.post(
                EXA_URL,
                json={
                    "query": query,
                    "numResults": 8,
                    "startPublishedDate": since,
                    "includeDomains": include_domains,
                    "type": "auto",
                },
            )
            r.raise_for_status()
        except httpx.HTTPError:
            return []
        return [
            RawItem(
                url=res.get("url"),
                title=res.get("title") or (res.get("text", "")[:200] if res.get("text") else None),
                source_type=self.source_type,
                source_name=source_name,
                author=res.get("author"),
                source_meta={"score": res.get("score")},
            )
            for res in r.json().get("results", [])
        ]
