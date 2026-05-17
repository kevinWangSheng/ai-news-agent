"""Processing orchestrator. Scheduler calls run_once() in-process."""
from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.db.models import Item
from app.db.session import get_session_factory
from app.processing.embed import embed_one
from app.processing.enricher import enrich_one
from app.processing.extract import extract_one
from app.processing.finalize import finalize_one

logger = logging.getLogger(__name__)


@dataclass
class StageStat:
    processed: int = 0
    succeeded: int = 0
    failed: int = 0


@dataclass
class ProcessingStats:
    extract: StageStat = field(default_factory=StageStat)
    enrich: StageStat = field(default_factory=StageStat)
    embed: StageStat = field(default_factory=StageStat)
    finalize: StageStat = field(default_factory=StageStat)


STAGES: list[tuple[str, str, Callable[[AsyncSession, Item], Awaitable[bool]]]] = [
    ("pending", "extract", extract_one),
    ("extracted", "enrich", enrich_one),
    ("enriched", "embed", embed_one),
    ("embedded", "finalize", finalize_one),
]


async def _run_stage(
    factory: async_sessionmaker[AsyncSession],
    queue_status: str,
    name: str,
    fn: Callable[[AsyncSession, Item], Awaitable[bool]],
    limit: int,
    concurrency: int,
) -> StageStat:
    stat = StageStat()
    s = get_settings()
    sem = asyncio.Semaphore(concurrency)

    async with factory() as session:
        rows = (
            await session.execute(
                select(Item)
                .where(Item.processing_status == queue_status)
                .where(Item.processing_attempts < s.processing_max_attempts)
                .limit(limit)
            )
        ).scalars().all()
        ids = [r.id for r in rows]

    async def _process(item_id: int) -> None:
        async with sem, factory() as session:
            item = await session.get(Item, item_id)
            if item is None:
                return
            stat.processed += 1
            try:
                ok = await fn(session, item)
            except Exception as exc:  # noqa: BLE001
                ok = False
                item.last_error = f"{type(exc).__name__}: {exc}"[:1000]
                logger.exception("stage=%s item=%s exception", name, item_id)
            if ok:
                stat.succeeded += 1
            else:
                stat.failed += 1
                item.processing_attempts = (item.processing_attempts or 0) + 1
                if item.processing_attempts >= s.processing_max_attempts:
                    item.processing_status = "failed"
            await session.commit()

    await asyncio.gather(*(_process(i) for i in ids))
    return stat


async def run_once(
    factory: async_sessionmaker[AsyncSession] | None = None, limit_per_stage: int = 50
) -> ProcessingStats:
    factory = factory or get_session_factory()
    s = get_settings()
    stats = ProcessingStats()
    field_map = {"extract": "extract", "enrich": "enrich", "embed": "embed", "finalize": "finalize"}
    for queue_status, name, fn in STAGES:
        result = await _run_stage(factory, queue_status, name, fn, limit_per_stage, s.processing_concurrency)
        setattr(stats, field_map[name], result)
        logger.info(
            "stage=%s processed=%d succeeded=%d failed=%d",
            name,
            result.processed,
            result.succeeded,
            result.failed,
        )
    return stats


async def run_loop(
    factory: async_sessionmaker[AsyncSession] | None = None, interval_s: int = 60
) -> None:
    while True:
        try:
            await run_once(factory)
        except Exception:  # noqa: BLE001
            logger.exception("run_once raised")
        await asyncio.sleep(interval_s)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true")
    g.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.once:
        asyncio.run(run_once())
    else:
        asyncio.run(run_loop(interval_s=args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
