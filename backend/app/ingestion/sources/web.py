"""Web source ingestion.

Fetches a listing page, extracts same-host article links, then fetches each
article and uses trafilatura to turn HTML into markdown. HTTP is the fast path;
Playwright/Chromium is used for configured JS-rendered sites and as a fallback
when HTTP cannot fetch or expose enough HTML.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
import trafilatura

from app.ingestion.base import RawItem

logger = logging.getLogger(__name__)

DEFAULT_LINK_PATTERN = r"^/(blog|blogs|news|post|posts|p|article|articles|research|resources)/.+"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0 Safari/537.36 "
    "ai-agent-hub/0.1"
)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value.strip())


@dataclass
class WebSource:
    name: str
    listing_url: str
    fallback_urls: list[str] = field(default_factory=list)
    link_pattern: str = DEFAULT_LINK_PATTERN
    max_items: int = 15
    article_min_chars: int = 300
    source_type: str = "web"
    js_render: bool = False
    browser_wait_ms: int = 1500

    async def fetch(self) -> list[RawItem]:
        """Fetch listing and articles; failures are isolated per article."""
        listing_url = self.listing_url
        article_urls: list[str] = []
        for candidate_url in [self.listing_url, *self.fallback_urls]:
            try:
                listing_html = await self._fetch_listing(candidate_url)
            except Exception as exc:  # noqa: BLE001
                logger.info(
                    "source=%s listing fetch failed url=%s exc=%s",
                    self.name,
                    candidate_url,
                    exc,
                )
                continue
            article_urls = self._extract_article_urls(listing_html, listing_url=candidate_url)
            if not article_urls and not self.js_render:
                logger.info(
                    "source=%s no article links found via HTTP url=%s; trying Playwright",
                    self.name,
                    candidate_url,
                )
                listing_html = await self._fetch_with_playwright(candidate_url) or listing_html
                article_urls = self._extract_article_urls(listing_html, listing_url=candidate_url)
            if article_urls:
                listing_url = candidate_url
                break

        if not article_urls:
            logger.info("source=%s no article links found", self.name)
            return []

        items: list[RawItem] = []
        async with self._client() as client:
            for url in article_urls[: self.max_items]:
                try:
                    item = await self._fetch_article(url, client=client, listing_url=listing_url)
                except Exception as exc:  # noqa: BLE001 - isolate a single bad article
                    logger.info("source=%s article fetch failed url=%s exc=%s", self.name, url, exc)
                    continue
                if item is not None:
                    items.append(item)
        return items

    @staticmethod
    def _client() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=20,
            follow_redirects=True,
        )

    async def _fetch_listing(self, url: str) -> str:
        if self.js_render:
            html = await self._fetch_with_playwright(url)
            if html:
                return html
            logger.info("source=%s Playwright listing failed; falling back to HTTP", self.name)

        try:
            async with self._client() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError:
            html = await self._fetch_with_playwright(url)
            if html:
                return html
            raise

    async def _fetch_article(
        self,
        url: str,
        client: httpx.AsyncClient | None = None,
        listing_url: str | None = None,
    ) -> RawItem | None:
        html: str | None = None
        content_source = "web_http_trafilatura"

        if self.js_render:
            html = await self._fetch_with_playwright(url)
            if html:
                content_source = "web_playwright_trafilatura"

        if html is None:
            owns_client = client is None
            client = client or self._client()
            try:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
            except httpx.HTTPError:
                html = await self._fetch_with_playwright(url)
                content_source = "web_playwright_trafilatura"
            finally:
                if owns_client:
                    await client.aclose()

        if html is None:
            return None

        content_md = await _extract_markdown(html, url)
        if not content_md or len(content_md.strip()) < self.article_min_chars:
            fallback_html = await self._fetch_with_playwright(url)
            if fallback_html and fallback_html != html:
                html = fallback_html
                content_source = "web_playwright_trafilatura"
                content_md = await _extract_markdown(html, url)
            if not content_md or len(content_md.strip()) < self.article_min_chars:
                logger.info(
                    "source=%s article too short url=%s chars=%d",
                    self.name,
                    url,
                    len(content_md or ""),
                )
                return None

        title = _extract_title(html) or _title_from_url(url)
        author = _extract_meta(html, "author")
        published = _extract_datetime(html)

        return RawItem(
            url=url,
            title=title,
            source_type=self.source_type,
            source_name=self.name,
            author=author,
            published_at=published,
            content_md=content_md[:200_000],
            source_meta={
                "listing_url": listing_url or self.listing_url,
                "content_source": content_source,
            },
        )

    async def _fetch_with_playwright(self, url: str) -> str | None:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("playwright not installed; skipping browser fetch for %s", url)
            return None

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    page = await browser.new_page(user_agent=USER_AGENT)
                    await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                    try:
                        await page.wait_for_load_state("networkidle", timeout=5_000)
                    except Exception:
                        pass
                    if self.browser_wait_ms > 0:
                        await page.wait_for_timeout(self.browser_wait_ms)
                    return await page.content()
                finally:
                    await browser.close()
        except Exception as exc:  # noqa: BLE001
            logger.info("playwright fetch failed source=%s url=%s exc=%s", self.name, url, exc)
            return None

    def _extract_article_urls(self, html: str, listing_url: str | None = None) -> list[str]:
        parser = _LinkParser()
        parser.feed(html or "")

        base_url = listing_url or self.listing_url
        listing = urlsplit(base_url)
        listing_host = _host_key(listing.netloc)
        pattern = re.compile(self.link_pattern)
        seen: set[str] = set()
        urls: list[str] = []

        for raw_href in parser.hrefs:
            if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(base_url, raw_href)
            parsed = urlsplit(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            if _host_key(parsed.netloc) != listing_host:
                continue

            clean = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/") or "/", "", ""))
            if not _matches(pattern, raw_href, parsed.path, clean):
                continue
            if clean in seen or clean == base_url.rstrip("/"):
                continue
            seen.add(clean)
            urls.append(clean)

        return urls


def build_web_sources(cfg: dict[str, Any]) -> list[WebSource]:
    """Build enabled `type: web` sources from config.yaml's tech_sources buckets."""
    sources: list[WebSource] = []
    tech = cfg.get("tech_sources", {})
    for bucket_name in ("official_blogs", "expert_blogs", "aggregator_sources", "research_sources"):
        for entry in tech.get(bucket_name, []) or []:
            if entry.get("type") != "web" or entry.get("disabled") is True:
                continue
            if not entry.get("url"):
                continue
            sources.append(
                WebSource(
                    name=entry["name"],
                    listing_url=entry["url"],
                    fallback_urls=list(entry.get("fallback_urls") or []),
                    link_pattern=entry.get("link_pattern") or DEFAULT_LINK_PATTERN,
                    max_items=int(entry.get("max_items", 15)),
                    article_min_chars=int(entry.get("article_min_chars", 300)),
                    js_render=bool(entry.get("js_render", False)),
                )
            )
    return sources


def _host_key(netloc: str) -> str:
    host = netloc.lower().split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _matches(pattern: re.Pattern[str], href: str, path: str, url: str) -> bool:
    return bool(pattern.search(path) or pattern.search(href) or pattern.search(url))


async def _extract_markdown(html: str, url: str) -> str | None:
    return await asyncio.to_thread(
        trafilatura.extract,
        html,
        include_comments=False,
        include_tables=False,
        output_format="markdown",
        url=url,
    )


def _extract_meta(html: str, name: str) -> str | None:
    patterns = [
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(name)}["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(name)}["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return None


def _extract_title(html: str) -> str | None:
    for key in ("og:title", "twitter:title"):
        value = _extract_meta(html, key)
        if value:
            return value
    for pat in (r"<h1[^>]*>(.*?)</h1>", r"<title[^>]*>(.*?)</title>"):
        m = re.search(pat, html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            value = re.sub(r"<[^>]+>", " ", m.group(1))
            value = unescape(re.sub(r"\s+", " ", value)).strip()
            if value:
                return value
    return None


def _extract_datetime(html: str) -> datetime | None:
    for key in ("article:published_time", "date", "pubdate", "publish_date"):
        value = _extract_meta(html, key)
        if not value:
            continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def _title_from_url(url: str) -> str:
    path = urlsplit(url).path.rstrip("/").split("/")[-1]
    return re.sub(r"[-_]+", " ", path).strip().title() or url
