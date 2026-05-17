# Changelog

## v2.0.0 (2026-05-17) — ai-agent-hub

从 `ai-news-agent`(单向新闻聚合,GH Actions+邮件)升级为 `ai-agent-hub`(双向、持久、累积的个人 AI 信息中枢)。

### 升级路径(14 个 openspec change)

- **000 plan-corrections** — 12 处规划文档修订
- **001 foundation** — 仓库重构:`backend/` `frontend/` `cli/` `docker/`,旧代码迁到 `backend/legacy/`
- **002 data-model** — Postgres 16 + pgvector + tsvector,8 个表 + 3 个 trigger + HNSW 索引
- **002a source-tuning** — KOL handle 修正、`topics.yaml` 主题字典(34 个)、focus_keywords 自动生成(91 个)
- **003 ingestion-sources** — 6 个 source(RSS / GitHub / Exa / Twitter / 中文平台 / manual)+ `IngestionService` 幂等去重
- **004 processing-pipeline** — extract(trafilatura+playwright)→ enrich(Claude prompt cache)→ embed(Voyage-3 + OpenAI fallback)→ finalize
- **005 preference-scoring** — 基础分 + tag/entity/source boost + time decay + focus floor 6 + 冷启动门槛 50
- **006 rest-api** — 28 个端点(8 标签:ingest/items/search/topics/entities/digests/sources/health)
- **007 manual-ingest** — bookmarklet 安装页 + `hub` CLI(11 个子命令)
- **008-011 frontend** — Next.js 16 + SWR + cmdk;12 路由(inbox/library/topics+timeline/entities/digest/sources/settings/item)
- **012 scheduler-migration** — APScheduler + SQLAlchemyJobStore,9 个 job(替代 GH Actions)
- **013 decommission-old** — 删邮件依赖、重写 README + 本 changelog

### Breaking

- 不再有邮件 / Telegram 通道,改为 Web + CLI
- 不再有 GitHub Actions 调度,改为本地 APScheduler(`docker compose up -d scheduler`)
- 旧 `output/daily_report.md` 一次性产物退役,数据全部入 Postgres
- 配置:旧 `config/config.yaml` → `backend/config.yaml` + `backend/topics.yaml`;邮件/Telegram 环境变量删除

### 不破坏

- 6 个 source 的网络抓取逻辑完整迁移
- Claude prompt cache + MiniMax fallback 思路保留
- AI Agent 领域聚焦关键词扩展(原 12 → 91)

详见 [`docs/migration-from-v1.md`](docs/migration-from-v1.md)。

### v2.0.0 修补(2026-05-17 handoff)

- `backend/Dockerfile`:补 COPY `config.yaml` / `topics.yaml` / `alembic/` / `alembic.ini`(原版漏拷,容器内 `load_config()` 必 `FileNotFoundError`);加 HEALTHCHECK 走 `/health`
- `docker/docker-compose.yml`:新增 `migrate` 一次性服务执行 `alembic upgrade head`,`backend` / `scheduler` 用 `condition: service_completed_successfully` 等它
- `backend/app/ingestion/run.py`:移除 `load_config` / `load_topics` 的 legacy yaml fallback(canonical 与 legacy 100% 同步,fallback 是死代码且会让以后误删 backend yaml 时静默回退)
- `docs/handoff.md`:新增,装好 docker 后按 10 节顺序跑可收口 7 个 change 的 verify 挂账
