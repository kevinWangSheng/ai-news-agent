"""Entities."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import EntityOut, ItemOut
from app.db.models import Entity, Item, ItemEntity
from app.db.session import get_db

router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("", response_model=list[EntityOut])
async def list_entities(
    type: str | None = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[EntityOut]:
    stmt = select(Entity).order_by(Entity.last_item_at.desc().nullslast()).limit(limit)
    if type:
        stmt = stmt.where(Entity.type == type)
    rows = (await db.execute(stmt)).scalars().all()
    return [EntityOut.model_validate(e, from_attributes=True) for e in rows]


@router.get("/{slug}", response_model=EntityOut)
async def get_entity(slug: str, db: AsyncSession = Depends(get_db)) -> EntityOut:
    e = (await db.execute(select(Entity).where(Entity.slug == slug))).scalar_one_or_none()
    if e is None:
        raise HTTPException(404, "entity not found")
    return EntityOut.model_validate(e, from_attributes=True)


@router.get("/{slug}/items", response_model=list[ItemOut])
async def entity_items(
    slug: str, limit: int = Query(50, le=200), db: AsyncSession = Depends(get_db)
) -> list[ItemOut]:
    items = (
        await db.execute(
            select(Item)
            .join(ItemEntity, ItemEntity.item_id == Item.id)
            .join(Entity, Entity.id == ItemEntity.entity_id)
            .where(Entity.slug == slug)
            .order_by(Item.published_at.desc().nullslast())
            .limit(limit)
        )
    ).scalars().all()
    return [ItemOut.model_validate(i, from_attributes=True) for i in items]
