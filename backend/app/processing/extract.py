"""Stage 1: fetch full content (trafilatura, playwright fallback)."""
from __future__ import annotations

import asyncio
import logging

import httpx
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

    text = await _fetch_via_trafilatura(item.url)
    if text is None:
        text = await _fetch_via_playwright(item.url)

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
    return await asyncio.to_thread(trafilatura.extract, r.text, include_comments=False, output_format="markdown")


async def _fetch_via_playwright(url: str) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("playwright not installed; skipping JS fallback for %s", url)
        return None

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                html = await page.content()
            finally:
                await browser.close()
    except Exception as exc:  # noqa: BLE001
        logger.info("playwright fallback fail %s: %s", url, exc)
        return None

    return await asyncio.to_thread(trafilatura.extract, html, include_comments=False, output_format="markdown")
