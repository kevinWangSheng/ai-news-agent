"""Topics CRUD + timeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ItemOut, TopicCreate, TopicOut, TopicPatch
from app.db.models import Item, ItemTopic, Topic
from app.db.session import get_db

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
async def list_topics(
    limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)
) -> list[TopicOut]:
    rows = (
        await db.execute(
            select(Topic).order_by(Topic.is_pinned.desc(), Topic.last_item_at.desc().nullslast()).limit(limit)
        )
    ).scalars().all()
    return [TopicOut.model_validate(t, from_attributes=True) for t in rows]


@router.post("", response_model=TopicOut)
async def create_topic(req: TopicCreate, db: AsyncSession = Depends(get_db)) -> TopicOut:
    t = Topic(
        slug=req.slug,
        name_zh=req.name_zh,
        name_en=req.name_en,
        description=req.description,
        watch_keywords=req.watch_keywords or None,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return TopicOut.model_validate(t, from_attributes=True)


@router.patch("/{slug}", response_model=TopicOut)
async def patch_topic(slug: str, patch: TopicPatch, db: AsyncSession = Depends(get_db)) -> TopicOut:
    t = (await db.execute(select(Topic).where(Topic.slug == slug))).scalar_one_or_none()
    if t is None:
        raise HTTPException(404, "topic not found")
    if patch.name_zh is not None:
        t.name_zh = patch.name_zh
    if patch.description is not None:
        t.description = patch.description
    if patch.watch_keywords is not None:
        t.watch_keywords = patch.watch_keywords or None
    if patch.is_pinned is not None:
        t.is_pinned = patch.is_pinned
    await db.commit()
    await db.refresh(t)
    return TopicOut.model_validate(t, from_attributes=True)


@router.get("/{slug}/items", response_model=list[ItemOut])
async def topic_items(
    slug: str, limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)
) -> list[ItemOut]:
    items = (
        await db.execute(
            select(Item)
            .join(ItemTopic, ItemTopic.item_id == Item.id)
            .join(Topic, Topic.id == ItemTopic.topic_id)
            .where(Topic.slug == slug)
            .order_by(Item.published_at.desc().nullslast())
            .limit(limit)
        )
    ).scalars().all()
    return [ItemOut.model_validate(i, from_attributes=True) for i in items]


@router.get("/{slug}/timeline")
async def topic_timeline(
    slug: str, bucket: str = "month", db: AsyncSession = Depends(get_db)
) -> list[dict]:
    truncator = "month" if bucket == "month" else "week"
    rows = (
        await db.execute(
            select(
                func.date_trunc(truncator, Item.published_at).label("bucket"),
                func.count().label("n"),
            )
            .join(ItemTopic, ItemTopic.item_id == Item.id)
            .join(Topic, Topic.id == ItemTopic.topic_id)
            .where(Topic.slug == slug)
            .group_by(func.date_trunc(truncator, Item.published_at))
            .order_by(func.date_trunc(truncator, Item.published_at).desc())
            .limit(36)
        )
    ).all()
    return [{"bucket": b.isoformat() if b else None, "count": int(n)} for b, n in rows]
