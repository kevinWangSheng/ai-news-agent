"""Items CRUD + interactions."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.cursor import decode, encode
from app.api.schemas import (
    EntityOut,
    InteractionRequest,
    ItemDetail,
    ItemOut,
    ItemPatch,
    Page,
    TopicOut,
)
from app.db.models import Entity, Interaction, Item, ItemEntity, ItemTopic, Topic
from app.db.session import get_db

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=Page)
async def list_items(
    status: str | None = None,
    source_type: str | None = None,
    source_name: str | None = None,
    topic: str | None = Query(None, description="topic slug"),
    entity: str | None = Query(None, description="entity slug"),
    min_score: float | None = None,
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = None,
    cursor: str | None = None,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page:
    stmt = select(Item)
    if status:
        stmt = stmt.where(Item.status == status)
    if source_type:
        stmt = stmt.where(Item.source_type == source_type)
    if source_name:
        stmt = stmt.where(Item.source_name == source_name)
    if min_score is not None:
        stmt = stmt.where(Item.final_score >= min_score)
    if from_:
        stmt = stmt.where(Item.published_at >= from_)
    if to:
        stmt = stmt.where(Item.published_at <= to)
    if topic:
        stmt = stmt.join(ItemTopic, ItemTopic.item_id == Item.id).join(
            Topic, Topic.id == ItemTopic.topic_id
        ).where(Topic.slug == topic)
    if entity:
        stmt = stmt.join(ItemEntity, ItemEntity.item_id == Item.id).join(
            Entity, Entity.id == ItemEntity.entity_id
        ).where(Entity.slug == entity)

    cursor_data = decode(cursor)
    if cursor_data:
        ts, last_id = cursor_data
        stmt = stmt.where(
            (Item.created_at < ts) | and_(Item.created_at == ts, Item.id < last_id)
        )

    rows = (
        await db.execute(stmt.order_by(Item.created_at.desc(), Item.id.desc()).limit(limit + 1))
    ).scalars().all()

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = (
        encode(page_rows[-1].created_at, page_rows[-1].id) if has_more and page_rows else None
    )
    return Page(items=[ItemOut.model_validate(i, from_attributes=True) for i in page_rows], next_cursor=next_cursor)


@router.get("/{item_id}", response_model=ItemDetail)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)) -> ItemDetail:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")

    topics = (
        await db.execute(
            select(Topic).join(ItemTopic, ItemTopic.topic_id == Topic.id).where(
                ItemTopic.item_id == item_id
            )
        )
    ).scalars().all()
    entities = (
        await db.execute(
            select(Entity).join(ItemEntity, ItemEntity.entity_id == Entity.id).where(
                ItemEntity.item_id == item_id
            )
        )
    ).scalars().all()

    related: list[Item] = []
    if item.embedding is not None:
        related = (
            await db.execute(
                select(Item)
                .where(Item.id != item.id)
                .where(Item.embedding.is_not(None))
                .order_by(Item.embedding.cosine_distance(item.embedding))
                .limit(5)
            )
        ).scalars().all()

    return ItemDetail(
        **ItemOut.model_validate(item, from_attributes=True).model_dump(),
        content_md=item.content_md,
        score_breakdown=item.score_breakdown,
        topics=[TopicOut.model_validate(t, from_attributes=True) for t in topics],
        entities=[EntityOut.model_validate(e, from_attributes=True) for e in entities],
        related_items=[ItemOut.model_validate(r, from_attributes=True) for r in related],
    )


@router.patch("/{item_id}", response_model=ItemOut)
async def patch_item(item_id: int, patch: ItemPatch, db: AsyncSession = Depends(get_db)) -> ItemOut:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    if patch.status is not None:
        item.status = patch.status
    if patch.user_note is not None:
        item.user_note = patch.user_note
    if patch.tags is not None:
        item.tags = patch.tags
    await db.commit()
    await db.refresh(item)
    return ItemOut.model_validate(item, from_attributes=True)


@router.delete("/{item_id}", response_model=ItemOut)
async def soft_delete(item_id: int, db: AsyncSession = Depends(get_db)) -> ItemOut:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    item.status = "trashed"
    await db.commit()
    await db.refresh(item)
    return ItemOut.model_validate(item, from_attributes=True)


@router.post("/{item_id}/interactions")
async def add_interaction(
    item_id: int, req: InteractionRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    item = await db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    inter = Interaction(
        item_id=item_id,
        action=req.action,
        dwell_seconds=req.dwell_seconds,
        note_text=req.note_text,
        highlight_text=req.highlight_text,
    )
    db.add(inter)
    # auto-progress item status for common actions
    if req.action == "keep":
        item.status = "kept"
    elif req.action == "archive":
        item.status = "archived"
    elif req.action == "trash":
        item.status = "trashed"
    if req.note_text:
        item.user_note = req.note_text
    await db.commit()
    await db.refresh(inter)
    return {"id": inter.id}
