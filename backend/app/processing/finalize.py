"""Stage 4: finalize score using preference engine (005 Task 11)."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item
from app.scoring.preference import compute_preference_delta


async def finalize_one(session: AsyncSession, item: Item) -> bool:
    if item.quality_score is None:
        item.processing_status = "ready"
        return True
    delta, breakdown = await compute_preference_delta(session, item)
    final = max(0.0, min(10.0, float(item.quality_score) + delta))
    item.final_score = final
    item.score_breakdown = breakdown
    item.processing_status = "ready"
    return True
