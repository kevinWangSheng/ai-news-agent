"""Stage 1: fetch full content (trafilatura, playwright fallback)."""
from __future__ import annotations

import asyncio
import logging
import re
from html import unescape

import httpx
import lxml.html
import trafilatura
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item

logger = logging.getLogger(__name__)


async def extract_one(session: AsyncSession, item: Item) -> bool:
    if item.source_type == "manual" and not item.url:
        item.processing_status = "extracted"
        return True

    if not item.url:
        item.processing_status = "extracted"
        return True

    if item.content_md and len(item.content_md.strip()) >= 300:
        item.processing_status = "extracted"
        return True

    text = await _fetch_via_trafilatura(item.url)
    if text is None:
        text = await _fetch_via_playwright(item.url)

    if text is None and item.source_type == "github":
        fallback = _github_description_fallback(item)
        if fallback:
            text = fallback

    if text is None:
        text = _metadata_content_fallback(item)

    if text is None:
        return False

    item.content_md = text[:200_000]
    item.processing_status = "extracted"
    return True


async def _fetch_via_trafilatura(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(
            timeout=20, follow_redirects=True, headers={"User-Agent": "ai-agent-hub/0.1"}
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
    except httpx.HTTPError as exc:
        logger.info("trafilatura http fail %s: %s", url, exc)
        return None
    return await asyncio.to_thread(_extract_html_text, r.text)


async def _fetch_via_playwright(url: str) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("playwright not installed; skipping JS fallback for %s", url)
        return None

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0 Safari/537.36 "
                        "ai-agent-hub/0.1"
                    )
                )
                await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                try:
                    await page.wait_for_load_state("networkidle", timeout=5_000)
                except Exception:
                    pass
                await page.wait_for_timeout(1500)
                html = await page.content()
            finally:
                await browser.close()
    except Exception as exc:  # noqa: BLE001
        logger.info("playwright fallback fail %s: %s", url, exc)
        return None

    return await asyncio.to_thread(_extract_html_text, html)


def _extract_html_text(html: str) -> str | None:
    text = trafilatura.extract(html, include_comments=False, output_format="markdown")
    if text and len(text.strip()) >= 300:
        return text

    fallback = _structured_text_fallback(html)
    if fallback and len(fallback.strip()) > len((text or "").strip()):
        return fallback
    return text


def _structured_text_fallback(html: str) -> str | None:
    """Fallback for pages whose readable content is in obvious article containers.

    Some newsletter archives (notably Buttondown) expose a clean `<article>` or
    `.email-body` but are missed by trafilatura. XPath + text_content gives us a
    deterministic local fallback without adding another dependency.
    """
    try:
        doc = lxml.html.fromstring(html)
    except Exception:
        return None

    candidates = doc.xpath(
        "//*[self::article or self::main "
        "or contains(concat(' ', normalize-space(@class), ' '), ' email-body ') "
        "or contains(concat(' ', normalize-space(@class), ' '), ' markdown ') "
        "or contains(concat(' ', normalize-space(@class), ' '), ' post-content ')]"
    )
    best = ""
    for el in candidates:
        text = _clean_text(el.text_content())
        if len(text) > len(best):
            best = text
    return best or None


def _github_description_fallback(item: Item) -> str | None:
    """Use GitHub API metadata when README extraction repeatedly fails.

    GitHub repository pages are often HTML shells or rate-limited in extraction. The
    ingestion title already carries `owner/repo — description`; preserving that is
    better than burning all retries and marking the item failed.
    """
    if not item.title:
        return None
    meta = item.source_meta or {}
    parts = [item.title.strip()]
    if meta.get("stars") is not None:
        parts.append(f"Stars: {meta.get('stars')}")
    if meta.get("language"):
        parts.append(f"Language: {meta.get('language')}")
    if meta.get("topic"):
        parts.append(f"Topic: {meta.get('topic')}")
    return "\n\n".join(parts)


def _metadata_content_fallback(item: Item) -> str | None:
    """Use source metadata/title when article-page extraction is impossible.

    RSS feeds often carry useful summaries even when the article page is blocked
    or JS-heavy. Manual smoke items may also intentionally provide only a title.
    This fallback keeps such items processable instead of burning all retries.
    """
    meta = item.source_meta or {}
    raw_summary = meta.get("raw_summary") if isinstance(meta, dict) else None
    summary = _plain_text(raw_summary or "")

    parts: list[str] = []
    if item.title:
        parts.append(item.title.strip())
    if summary and summary not in parts:
        parts.append(summary)
    if item.url and (item.source_type == "manual" or not summary):
        parts.append(f"URL: {item.url}")

    if item.source_type in {"rss", "manual"} and parts:
        return "\n\n".join(parts)
    return None


def _plain_text(value: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return _clean_text(text)


def _clean_text(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    compact_lines = [line for line in lines if line]
    if compact_lines:
        return "\n\n".join(compact_lines)
    return re.sub(r"\s+", " ", value).strip()
