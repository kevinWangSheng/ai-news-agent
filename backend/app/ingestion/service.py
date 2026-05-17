"""Persist raw items + record errors."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IngestionError, Item
from app.ingestion.base import RawItem
from app.ingestion.normalize import normalize_url

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_item(self, raw: RawItem) -> tuple[Item, bool]:
        """Returns (item, created). Idempotent on url_normalized."""
        url_norm = normalize_url(raw.url)

        if url_norm:
            existing = (
                await self.session.execute(
                    select(Item).where(Item.url_normalized == url_norm)
                )
            ).scalar_one_or_none()
            if existing:
                return existing, False

        item = Item(
            url=raw.url,
            url_normalized=url_norm,
            title=raw.title,
            content_md=raw.content_md,
            source_type=raw.source_type,
            source_name=raw.source_name,
            source_meta=raw.source_meta or None,
            author=raw.author,
            published_at=raw.published_at,
            status="inbox",
            processing_status="pending",
        )
        self.session.add(item)
        await self.session.flush()
        return item, True

    async def record_error(
        self,
        source_type: str,
        source_name: str,
        url: str | None,
        exc: BaseException,
    ) -> None:
        err = IngestionError(
            source_type=source_type,
            source_name=source_name,
            url=url,
            error_type=type(exc).__name__,
            error_msg=str(exc)[:1000],
        )
        self.session.add(err)
        await self.session.flush()
        logger.warning("ingestion error %s/%s url=%s exc=%s", source_type, source_name, url, exc)
