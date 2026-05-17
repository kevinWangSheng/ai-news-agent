"""Stage 3: embedding (Voyage primary, OpenAI fallback to 1024-d slice)."""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Item
from app.llm.client import get_openai, get_voyage

logger = logging.getLogger(__name__)

EMBED_DIM = 1024


async def embed_one(session: AsyncSession, item: Item) -> bool:
    text = " ".join(
        filter(None, [item.title_cn or item.title, item.summary_zh, " ".join(item.tags or [])])
    )[:2000]
    if not text:
        item.processing_status = "embedded"
        return True

    vec = await _voyage(text)
    if vec is None:
        vec = await _openai(text)
    if vec is None:
        return False

    item.embedding = vec
    item.processing_status = "embedded"
    return True


async def _voyage(text: str) -> list[float] | None:
    s = get_settings()
    if not s.voyage_api_key:
        return None
    try:
        client = get_voyage()
        resp = await client.embed([text], model="voyage-3", input_type="document")
        return list(resp.embeddings[0])
    except Exception as exc:  # noqa: BLE001
        logger.warning("voyage embed failed: %s", exc)
        return None


async def _openai(text: str) -> list[float] | None:
    s = get_settings()
    if not s.openai_api_key:
        return None
    try:
        client = get_openai()
        resp = await client.embeddings.create(model="text-embedding-3-small", input=text)
        full = resp.data[0].embedding  # 1536-d
        return list(full[:EMBED_DIM])
    except Exception as exc:  # noqa: BLE001
        logger.warning("openai embed fallback failed: %s", exc)
        return None
