"""In-memory last_run / last_success dict for /health/scheduler.

Trade-off: lost on scheduler restart, but avoids a separate persistence layer
since APScheduler already tracks job state in its SQLAlchemyJobStore.
"""
from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class JobRun(TypedDict, total=False):
    last_run: str
    last_success: str
    last_error: str | None


_RUNS: dict[str, JobRun] = {}


def record_start(name: str, ts: datetime) -> None:
    _RUNS.setdefault(name, {})["last_run"] = ts.isoformat()


def record_success(name: str, ts: datetime) -> None:
    _RUNS.setdefault(name, {})["last_success"] = ts.isoformat()
    _RUNS[name]["last_error"] = None


def record_failure(name: str, ts: datetime, err: str) -> None:
    _RUNS.setdefault(name, {})["last_error"] = err[:300]


def get_all() -> dict[str, JobRun]:
    return dict(_RUNS)
