# 012 · Scheduler Migration — Tasks

- [x] 1. backend 加 `apscheduler[sqlalchemy]` + `psycopg2-binary`(SQLAlchemyJobStore 用同步驱动)
  - 注:apscheduler 3.x 无 `asyncio` extra,直接用 `apscheduler[sqlalchemy]` + `AsyncIOScheduler`
- [x] 2. `backend/app/scheduler/__main__.py` — AsyncIOScheduler + SQLAlchemyJobStore(`postgresql+psycopg2://`) + `job_defaults={misfire_grace_time:300, coalesce:True}` + signal handler 优雅退出
- [x] 3. `backend/app/scheduler/jobs.py` — 9 个 job:
  - ingestion_rss `5 * * * *`,github `15 * * * *`,exa `25 */2 * * *`,twitter `35 */2 * * *`,chinese `45 */4 * * *`
  - processing_loop `interval(minutes=1)` 直接 `from app.processing.run import run_once; await run_once(get_session_factory())`(同进程)
  - scoring_recompute `0 */2 * * *`
  - digest_daily `30 6 * * *`,digest_weekly `30 6 * * MON`
- [x] 4. `@track_run(name)` decorator — info log start/done duration + 异常 catch 不重抛 + 写 `app.scheduler.runs._RUNS` 内存 dict
- [x] 5. docker-compose scheduler entrypoint 改为 `python -m app.scheduler`
- [ ] 6. `/api/sources` 加 `next_run_at` 字段 — scheduler 在另一进程,需要跨进程访问 jobstore,推迟到真有 docker 部署再读 SQLAlchemyJobStore.apscheduler_jobs 表
- [x] 7. `/health/scheduler` 端点 — 读 `app.scheduler.runs.get_all()`(同 scheduler 进程才有数据;backend 进程返回空 dict,记 trade-off)
- [x] **额外** `backend/app/scheduler/digest_gen.py` — LLM 写 intro + ON CONFLICT 更新 digest 行(011 推迟到此处的活)
- [x] **verify** `build_scheduler()` 返回 9 jobs 通过
- [ ] 8-11. docker compose logs / 重启 / 24h 数据增长 verify — 需 docker

## 注意
- scheduler 进程内,无外部 broker(无 Redis)
- 错峰避免同时打满 LLM rate limit
- 所有 job 异常 catch 住,scheduler 不能死
- backend 进程的 `/health/scheduler` 是空 dict;真实数据在 scheduler 进程的内存。前端要看 next_run 需 backend 直接读 `apscheduler_jobs` 表
