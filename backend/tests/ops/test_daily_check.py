from types import SimpleNamespace

from app.ops.daily_check import _counter, _source_names
from app.scheduler.__main__ import build_scheduler


def test_counter_stringifies_empty_keys():
    assert _counter([("rss", 2), (None, 1)]) == {"rss": 2, "unknown": 1}


def test_source_names_prefers_source_name():
    rows = [
        SimpleNamespace(source_name="OpenAI Blog", source_type="rss"),
        SimpleNamespace(source_name=None, source_type="github"),
    ]
    assert _source_names(rows) == ["OpenAI Blog", "github"]


def test_scheduler_registers_ops_daily_check():
    sched = build_scheduler()
    job_ids = {job.id for job in sched.get_jobs()}
    assert "ops_daily_check" in job_ids
