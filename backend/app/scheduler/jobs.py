"""Scheduler jobs — all wrapped in @track_run."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Awaitable, Callable

from app.db.session import get_session_factory
from app.ingestion.run import build_sources, load_config, load_topics, run_source
from app.processing.run import run_once as processing_run_once
from app.scheduler.runs import record_failure, record_start, record_success
from app.scoring.recompute import recompute

logger = logging.getLogger(__name__)


def track_run(name: str):
    def deco(fn: Callable[[], Awaitable[None]]):
        @wraps(fn)
        async def wrapped():
            start = datetime.now(timezone.utc)
            record_start(name, start)
            logger.info("job=%s start", name)
            try:
                result = await fn()
            except Exception as exc:  # noqa: BLE001
                end = datetime.now(timezone.utc)
                record_failure(name, end, f"{type(exc).__name__}: {exc}")
                logger.exception("job=%s failed", name)
                return
            end = datetime.now(timezone.utc)
            record_success(name, end)
            duration = (end - start).total_seconds()
            logger.info("job=%s done duration=%.2fs result=%s", name, duration, result)
        return wrapped
    return deco


async def _run_kind(kind: str) -> dict:
    cfg = load_config()
    topics = load_topics()
    sources = build_sources(cfg, topics).get(kind, [])
    totals = {"fetched": 0, "created": 0, "deduped": 0}
    for s in sources:
        fetched, created, deduped = await run_source(s)
        totals["fetched"] += fetched
        totals["created"] += created
        totals["deduped"] += deduped
    return totals


@track_run("ingestion_rss")
async def ingestion_rss():
    return await _run_kind("rss")


@track_run("ingestion_web")
async def ingestion_web():
    return await _run_kind("web")


@track_run("ingestion_github")
async def ingestion_github():
    return await _run_kind("github")


@track_run("ingestion_exa_search")
async def ingestion_exa_search():
    return await _run_kind("exa_search")


@track_run("ingestion_twitter")
async def ingestion_twitter():
    return await _run_kind("twitter")


@track_run("ingestion_chinese")
async def ingestion_chinese():
    return await _run_kind("chinese")


@track_run("processing_loop")
async def processing_loop():
    stats = await processing_run_once(get_session_factory())
    return {"extract": stats.extract.succeeded, "enrich": stats.enrich.succeeded,
            "embed": stats.embed.succeeded, "finalize": stats.finalize.succeeded}


@track_run("scoring_recompute")
async def scoring_recompute():
    from datetime import timedelta
    n = await recompute(since=datetime.now(timezone.utc) - timedelta(hours=4))
    return {"updated": n}


@track_run("digest_daily")
async def digest_daily():
    from app.scheduler.digest_gen import generate_digest
    return await generate_digest(period="daily")


@track_run("digest_weekly")
async def digest_weekly():
    from app.scheduler.digest_gen import generate_digest
    return await generate_digest(period="weekly")


@track_run("ops_daily_check")
async def ops_daily_check():
    from app.ops.daily_check import run_check

    report = await run_check()
    return {
        "total": report["items"]["total"],
        "ready": report["items"]["processing_status"].get("ready", 0),
        "failed": report["issues"]["failed_count"],
        "non_ready": report["issues"]["non_ready_count"],
        "new": report["items"]["new"],
    }
