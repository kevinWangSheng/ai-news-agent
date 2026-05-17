"""Chinese platforms (微信公众号 / 知乎 / 少数派 / 36kr) via Exa.

Skeleton wrapping logic from legacy/agents/chinese_platform_agent.py.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from app.ingestion.base import RawItem

EXA_URL = "https://api.exa.ai/search"

CHINESE_DOMAINS = [
    "zhihu.com",
    "sspai.com",
    "36kr.com",
    "mp.weixin.qq.com",
    "qbitai.com",
    "jiqizhixin.com",
]


class ChineseSource:
    source_type = "chinese_platform"
    name = "chinese"

    def __init__(self, keywords: list[str], days_window: int = 5) -> None:
        self.keywords = keywords
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
            for kw in self.keywords:
                try:
                    r = await client.post(
                        EXA_URL,
                        json={
                            "query": kw,
                            "numResults": 6,
                            "startPublishedDate": since,
                            "includeDomains": CHINESE_DOMAINS,
                            "type": "auto",
                        },
                    )
                    r.raise_for_status()
                except httpx.HTTPError:
                    continue
                for res in r.json().get("results", []):
                    out.append(
                        RawItem(
                            url=res.get("url"),
                            title=res.get("title"),
                            source_type=self.source_type,
                            source_name="chinese",
                            author=res.get("author"),
                            source_meta={"score": res.get("score"), "query": kw},
                        )
                    )
        return out
