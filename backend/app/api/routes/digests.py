"""Digests — periodic curated picks (011 handles deeper digest generation)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import DigestOut
from app.db.models import Digest
from app.db.session import get_db

router = APIRouter(prefix="/api/digests", tags=["digests"])


@router.get("", response_model=list[DigestOut])
async def list_digests(
    period: str | None = Query(None, pattern="^(daily|weekly|topic)$"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[DigestOut]:
    stmt = select(Digest).order_by(Digest.generated_at.desc()).limit(limit)
    if period:
        stmt = stmt.where(Digest.period == period)
    rows = (await db.execute(stmt)).scalars().all()
    return [DigestOut.model_validate(d, from_attributes=True) for d in rows]


@router.get("/{period}/{period_key}", response_model=DigestOut)
async def get_digest(period: str, period_key: str, db: AsyncSession = Depends(get_db)) -> DigestOut:
    d = (
        await db.execute(
            select(Digest).where(Digest.period == period).where(Digest.period_key == period_key)
        )
    ).scalar_one_or_none()
    if d is None:
        raise HTTPException(404, "digest not found")
    return DigestOut.model_validate(d, from_attributes=True)


@router.post("/generate")
async def generate_digest(period: str = "daily", db: AsyncSession = Depends(get_db)) -> dict:
    # 011 will fill in LLM-driven intro + selection. Placeholder.
    return {"queued": True, "period": period, "note": "see 011-frontend-digest for full impl"}
