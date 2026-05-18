"""Author aggregations for 015 consumption UX."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import FacetCount, ItemOut
from app.db.models import Item
from app.db.session import get_db

router = APIRouter(prefix="/api/authors", tags=["authors"])


def _slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown"


@router.get("", response_model=list[FacetCount])
async def list_authors(limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)) -> list[FacetCount]:
    rows = (
        await db.execute(
            select(Item.author, func.count())
            .where(Item.author.is_not(None))
            .group_by(Item.author)
            .order_by(func.count().desc())
            .limit(limit)
        )
    ).all()
    return [FacetCount(value=name or "?", count=int(count)) for name, count in rows]


@router.get("/{slug}/items", response_model=list[ItemOut])
async def author_items(slug: str, limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)) -> list[ItemOut]:
    rows = (
        await db.execute(
            select(Item)
            .where(Item.author.is_not(None))
            .order_by(Item.published_at.desc().nullslast(), Item.created_at.desc())
            .limit(500)
        )
    ).scalars().all()
    items = [i for i in rows if i.author and _slugify(i.author) == slug][:limit]
    return [ItemOut.model_validate(i, from_attributes=True) for i in items]
