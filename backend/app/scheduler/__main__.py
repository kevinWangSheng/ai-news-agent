"""APScheduler entry. Run with: python -m app.scheduler"""
from __future__ import annotations

import asyncio
import logging
import signal

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.scheduler import jobs

logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncIOScheduler:
    s = get_settings()
    # APScheduler's SQLAlchemyJobStore needs a sync url; flip dialect.
    sync_url = s.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    sched = AsyncIOScheduler(
        jobstores={"default": SQLAlchemyJobStore(url=sync_url)},
        job_defaults={"misfire_grace_time": 300, "coalesce": True},
    )
    sched.add_job(jobs.ingestion_rss, CronTrigger.from_crontab("5 * * * *"), id="ingestion_rss", replace_existing=True)
    sched.add_job(jobs.ingestion_github, CronTrigger.from_crontab("15 * * * *"), id="ingestion_github", replace_existing=True)
    sched.add_job(jobs.ingestion_exa_search, CronTrigger.from_crontab("25 */2 * * *"), id="ingestion_exa_search", replace_existing=True)
    sched.add_job(jobs.ingestion_twitter, CronTrigger.from_crontab("35 */2 * * *"), id="ingestion_twitter", replace_existing=True)
    sched.add_job(jobs.ingestion_chinese, CronTrigger.from_crontab("45 */4 * * *"), id="ingestion_chinese", replace_existing=True)
    sched.add_job(jobs.processing_loop, IntervalTrigger(minutes=1), id="processing_loop", replace_existing=True)
    sched.add_job(jobs.scoring_recompute, CronTrigger.from_crontab("0 */2 * * *"), id="scoring_recompute", replace_existing=True)
    sched.add_job(jobs.digest_daily, CronTrigger.from_crontab("30 6 * * *"), id="digest_daily", replace_existing=True)
    sched.add_job(jobs.digest_weekly, CronTrigger.from_crontab("30 6 * * MON"), id="digest_weekly", replace_existing=True)
    return sched


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sched = build_scheduler()
    sched.start()
    logger.info("scheduler started, %d jobs", len(sched.get_jobs()))
    stop = asyncio.Event()

    def shutdown(*_):
        logger.info("shutdown signal")
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            asyncio.get_event_loop().add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass  # Windows

    await stop.wait()
    sched.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
