"""Hybrid / fulltext / semantic search."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import FacetCount, ItemOut, SearchResponse
from app.db.models import Item
from app.db.session import get_db
from app.config import get_settings
from app.llm.client import get_ark, get_openai, get_voyage

router = APIRouter(prefix="/api/search", tags=["search"])


async def _embed_query(q: str) -> list[float] | None:
    """Embed a search query with the same provider order as processing: ARK → Voyage → OpenAI."""
    s = get_settings()
    if s.ark_api_key:
        try:
            resp = await get_ark().embeddings.create(
                model=s.ark_embed_model, input=q, dimensions=1024
            )
            return list(resp.data[0].embedding)
        except Exception:
            pass
    if s.voyage_api_key:
        try:
            resp = await get_voyage().embed([q], model="voyage-3", input_type="query")
            return list(resp.embeddings[0])
        except Exception:
            pass
    if s.openai_api_key:
        try:
            resp = await get_openai().embeddings.create(
                model="text-embedding-3-small", input=q, dimensions=1024
            )
            return list(resp.data[0].embedding)
        except Exception:
            pass
    return None


@router.get("", response_model=SearchResponse)
async def search(
    q: str,
    mode: str = Query("hybrid", pattern="^(hybrid|fulltext|semantic)$"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    if mode in ("fulltext", "hybrid"):
        ft_stmt = (
            select(Item, func.ts_rank(Item.search_vector, func.websearch_to_tsquery("simple", q)).label("rank"))
            .where(Item.search_vector.op("@@")(func.websearch_to_tsquery("simple", q)))
            .order_by(text("rank DESC"), Item.final_score.desc().nullslast())
            .limit(limit * 2 if mode == "hybrid" else limit)
        )
        ft_rows = (await db.execute(ft_stmt)).all()
    else:
        ft_rows = []

    semantic_rows = []
    if mode in ("semantic", "hybrid"):
        vec = await _embed_query(q)
        if vec is not None:
            sem_stmt = (
                select(Item)
                .where(Item.embedding.is_not(None))
                .order_by(Item.embedding.cosine_distance(vec))
                .limit(limit * 2 if mode == "hybrid" else limit)
            )
            semantic_rows = [(r, 0.0) for r in (await db.execute(sem_stmt)).scalars().all()]
        elif mode == "semantic":
            raise HTTPException(503, "embedding service unavailable")

    if mode == "hybrid":
        items = _rrf_merge(ft_rows, semantic_rows, k=60)[:limit]
    elif mode == "semantic":
        items = [r for r, _ in semantic_rows][:limit]
    else:
        items = [r for r, _ in ft_rows][:limit]

    sources = (
        await db.execute(
            select(Item.source_name, func.count())
            .where(Item.id.in_([i.id for i in items]) if items else False)
            .group_by(Item.source_name)
        )
    ).all() if items else []
    facets = {
        "sources": [FacetCount(value=name or "?", count=int(n)) for name, n in sources],
    }

    return SearchResponse(
        total=len(items),
        items=[ItemOut.model_validate(i, from_attributes=True) for i in items],
        facets=facets,
    )


def _rrf_merge(ft_rows, semantic_rows, k: int = 60) -> list[Item]:
    scores: dict[int, float] = {}
    keep: dict[int, Item] = {}
    for rank, (it, _) in enumerate(ft_rows, start=1):
        scores[it.id] = scores.get(it.id, 0.0) + 1.0 / (k + rank)
        keep[it.id] = it
    for rank, (it, _) in enumerate(semantic_rows, start=1):
        scores[it.id] = scores.get(it.id, 0.0) + 1.0 / (k + rank)
        keep[it.id] = it
    for iid in keep:
        if keep[iid].final_score is not None:
            scores[iid] += float(keep[iid].final_score) / 100.0
    return [keep[iid] for iid in sorted(scores, key=lambda x: scores[x], reverse=True)]
