"""Daily operational health check for the content pipeline."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.tier import resolve_tier
from app.db.models import IngestionError, Item
from app.db.session import get_session_factory
from app.ranking import diversify_ranked_items

logger = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def _counter(rows: list[tuple[Any, int]]) -> dict[str, int]:
    return {str(key or "unknown"): int(value) for key, value in rows}


def _source_names(items: list[Item], limit: int = 8) -> list[str]:
    return [item.source_name or item.source_type for item in items[:limit]]


async def _group_count(
    db: AsyncSession,
    column,
    *where_clauses,
    limit: int | None = None,
) -> dict[str, int]:
    stmt = select(column, func.count()).select_from(Item).group_by(column).order_by(func.count().desc())
    for clause in where_clauses:
        stmt = stmt.where(clause)
    if limit is not None:
        stmt = stmt.limit(limit)
    return _counter(list((await db.execute(stmt)).all()))


async def collect_report(db: AsyncSession, *, window_hours: int = 24, lane_limit: int = 20) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=window_hours)

    status_rows = list(
        (
            await db.execute(
                select(Item.processing_status, func.count())
                .select_from(Item)
                .group_by(Item.processing_status)
                .order_by(Item.processing_status)
            )
        ).all()
    )
    processing_status = _counter(status_rows)

    total = int((await db.execute(select(func.count()).select_from(Item))).scalar_one() or 0)
    scored = int(
        (
            await db.execute(
                select(func.count()).select_from(Item).where(Item.final_score.is_not(None))
            )
        ).scalar_one()
        or 0
    )
    new_24h = int(
        (
            await db.execute(
                select(func.count()).select_from(Item).where(Item.ingested_at >= since)
            )
        ).scalar_one()
        or 0
    )

    new_by_type = await _group_count(db, Item.source_type, Item.ingested_at >= since)
    new_by_source = await _group_count(db, Item.source_name, Item.ingested_at >= since, limit=12)

    raw_top50_rows = (
        await db.execute(
            select(Item)
            .where(Item.status == "inbox")
            .where(Item.processing_status == "ready")
            .order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(50)
        )
    ).scalars().all()
    raw_top50_type = dict(Counter(item.source_type or "unknown" for item in raw_top50_rows))
    raw_top50_source = dict(Counter(item.source_name or "unknown" for item in raw_top50_rows).most_common(12))

    lane_candidate_limit = min(1000, lane_limit * 10)
    top_rows = (
        await db.execute(
            select(Item)
            .where(Item.status == "inbox")
            .where(Item.processing_status == "ready")
            .order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(lane_candidate_limit)
        )
    ).scalars().all()
    top_signals = diversify_ranked_items(top_rows, lane_limit)

    official_values = resolve_tier("official")[1]  # type: ignore[index]
    official_rows = (
        await db.execute(
            select(Item)
            .where(Item.status == "inbox")
            .where(Item.processing_status == "ready")
            .where(Item.source_name.in_(official_values))
            .order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(min(500, lane_limit * 8))
        )
    ).scalars().all()
    official_updates = diversify_ranked_items(
        official_rows,
        lane_limit,
        type_caps={},
        source_cap=max(2, int(lane_limit * 0.12)),
        backfill=False,
    )

    repo_rows = (
        await db.execute(
            select(Item)
            .where(Item.status == "inbox")
            .where(Item.processing_status == "ready")
            .where(Item.source_type == "github")
            .order_by(Item.final_score.desc().nullslast(), Item.created_at.desc(), Item.id.desc())
            .limit(min(500, lane_limit * 8))
        )
    ).scalars().all()
    repo_radar = diversify_ranked_items(
        repo_rows,
        lane_limit,
        type_caps={},
        source_cap=max(3, int(lane_limit * 0.18)),
        backfill=False,
    )

    failed_items = (
        await db.execute(
            select(Item)
            .where(Item.processing_status == "failed")
            .order_by(Item.ingested_at.desc())
            .limit(10)
        )
    ).scalars().all()
    non_ready_items = (
        await db.execute(
            select(Item)
            .where(Item.processing_status.not_in(["ready", "failed"]))
            .order_by(Item.ingested_at.desc())
            .limit(10)
        )
    ).scalars().all()
    ingestion_errors_24h = int(
        (
            await db.execute(
                select(func.count()).select_from(IngestionError).where(IngestionError.created_at >= since)
            )
        ).scalar_one()
        or 0
    )

    return {
        "checked_at": now,
        "window_hours": window_hours,
        "items": {
            "total": total,
            "scored": scored,
            "new": new_24h,
            "processing_status": processing_status,
            "new_by_type": new_by_type,
            "new_by_source": new_by_source,
        },
        "raw_top50": {
            "by_type": raw_top50_type,
            "by_source": raw_top50_source,
        },
        "lanes": {
            "top_signals": _source_names(top_signals),
            "official_updates": _source_names(official_updates),
            "repo_radar": _source_names(repo_radar),
        },
        "issues": {
            "failed_count": processing_status.get("failed", 0),
            "non_ready_count": sum(
                value for key, value in processing_status.items() if key not in {"ready", "failed"}
            ),
            "ingestion_errors_24h": ingestion_errors_24h,
            "failed_items": [
                {
                    "id": item.id,
                    "source": item.source_name,
                    "title": item.title_cn or item.title,
                    "attempts": item.processing_attempts,
                    "last_error": item.last_error,
                }
                for item in failed_items
            ],
            "non_ready_items": [
                {
                    "id": item.id,
                    "source": item.source_name,
                    "title": item.title_cn or item.title,
                    "processing_status": item.processing_status,
                    "attempts": item.processing_attempts,
                }
                for item in non_ready_items
            ],
        },
    }


def log_report(report: dict[str, Any]) -> None:
    items = report["items"]
    issues = report["issues"]
    logger.info(
        "ops_daily_check totals total=%s ready=%s failed=%s non_ready=%s scored=%s new_%sh=%s",
        items["total"],
        items["processing_status"].get("ready", 0),
        issues["failed_count"],
        issues["non_ready_count"],
        items["scored"],
        report["window_hours"],
        items["new"],
    )
    logger.info(
        "ops_daily_check new_by_type=%s new_by_source=%s",
        items["new_by_type"],
        items["new_by_source"],
    )
    logger.info(
        "ops_daily_check raw_top50_by_type=%s raw_top50_by_source=%s",
        report["raw_top50"]["by_type"],
        report["raw_top50"]["by_source"],
    )
    logger.info(
        "ops_daily_check lanes top=%s official=%s repo=%s",
        report["lanes"]["top_signals"],
        report["lanes"]["official_updates"],
        report["lanes"]["repo_radar"],
    )
    if issues["failed_count"] or issues["non_ready_count"] or issues["ingestion_errors_24h"]:
        logger.warning(
            "ops_daily_check issues failed=%s non_ready=%s ingestion_errors_%sh=%s failed_items=%s non_ready_items=%s",
            issues["failed_count"],
            issues["non_ready_count"],
            report["window_hours"],
            issues["ingestion_errors_24h"],
            issues["failed_items"],
            issues["non_ready_items"],
        )
    else:
        logger.info("ops_daily_check issues none")


async def run_check(*, window_hours: int = 24, lane_limit: int = 20) -> dict[str, Any]:
    async with get_session_factory()() as db:
        report = await collect_report(db, window_hours=window_hours, lane_limit=lane_limit)
    log_report(report)
    return report


async def _amain() -> None:
    parser = argparse.ArgumentParser(description="Run the AI news agent daily operational check.")
    parser.add_argument("--window-hours", type=int, default=24)
    parser.add_argument("--lane-limit", type=int, default=20)
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    report = await run_check(window_hours=args.window_hours, lane_limit=args.lane_limit)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default))


if __name__ == "__main__":
    asyncio.run(_amain())
