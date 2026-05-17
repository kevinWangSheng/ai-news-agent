"""GitHub source — trending / topics / rising_stars / new_projects.

Skeleton wrapping logic from legacy/agents/github_agent.py. Uses GitHub public API.
"""
from __future__ import annotations

import os
from datetime import datetime

import httpx

from app.ingestion.base import RawItem

GITHUB_API = "https://api.github.com"


class GitHubSource:
    source_type = "github"
    name = "github"

    def __init__(self, topics: list[str], stars_threshold: int = 100) -> None:
        self.topics = topics
        self.stars_threshold = stars_threshold

    async def fetch(self) -> list[RawItem]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        items: list[RawItem] = []
        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            for topic in self.topics:
                q = f"topic:{topic} stars:>{self.stars_threshold}"
                try:
                    r = await client.get(
                        f"{GITHUB_API}/search/repositories",
                        params={"q": q, "sort": "updated", "per_page": 20},
                    )
                    r.raise_for_status()
                except httpx.HTTPError:
                    continue
                for repo in r.json().get("items", []):
                    items.append(
                        RawItem(
                            url=repo["html_url"],
                            title=f"{repo['full_name']} — {repo.get('description') or ''}",
                            source_type=self.source_type,
                            source_name=f"github:{topic}",
                            author=repo["owner"]["login"],
                            published_at=_parse(repo.get("pushed_at")),
                            source_meta={
                                "stars": repo.get("stargazers_count"),
                                "language": repo.get("language"),
                                "topic": topic,
                            },
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
