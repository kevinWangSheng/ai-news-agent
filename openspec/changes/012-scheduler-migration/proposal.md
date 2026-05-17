# 012 · Scheduler Migration(替代 GitHub Actions)

**Status: completed (2026-05-17)** — 9 jobs 注册成功 + digest LLM 生成 + SQLAlchemyJobStore 持久化;真实运行 verify 需 docker

## 背景
旧系统靠 GitHub Actions 每天 08:00 / 20:00 跑,推邮件。新系统是本地常驻服务,调度也常驻。

## 目标
- 使用 APScheduler(进程内)实现定时任务
- 任务清单:
  - 每 1h 跑 ingestion(各 source 错峰)
  - 每 1m 跑 processing(队列消费)
  - 每 1h 跑 scoring recompute --since 7d(轻量重算)
  - 每天 06:30 生成 daily digest
  - 每周一 06:30 生成 weekly digest
- 启动入口:`python -m app.scheduler` (docker compose 第 4 个 service)

## 验收
- [ ] `docker compose up` 后 scheduler service healthy 且按 schedule 跑任务
- [ ] 日志可见每次任务的开始 / 结束 / 耗时 / 失败计数
- [ ] 手动 trigger:`POST /api/sources/{name}/trigger` 与 scheduler 独立工作
- [ ] 重启 scheduler 不丢任务(进程内调度,重启后下次到点继续)
