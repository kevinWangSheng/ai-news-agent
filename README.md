# ai-agent-hub

> 个人 AI 信息中枢 —— 双向、持久、累积。把感兴趣的东西扔进去,系统会记得读过/标记过什么,并据此推送、检索、按主题/实体/时间检索。

> v2.0(WIP)正在从 `ai-news-agent` 单向新闻聚合升级而来。完整的升级规划见 [`openspec/README.md`](openspec/README.md)。

## 架构

```
投喂层      bookmarklet / `hub` CLI / 6 个 ingestion source
   ↓
处理流水线   trafilatura/playwright 抓全文 → Claude enrich → Voyage embedding → 评分
   ↓
存储        Postgres 16 + pgvector + tsvector(items / topics / entities / interactions / digests)
   ↓
消费层      FastAPI REST + Next.js Web(/inbox /library /topics /entities /digest)
```

## 一键启动

```bash
cd docker
cp .env.example .env   # 填入 ANTHROPIC_API_KEY / VOYAGE_API_KEY 等
docker compose up -d --build
# migrate 一次性服务自动跑 alembic upgrade head;backend / scheduler 在 migrate 完成后启动
# backend → http://localhost:8000  · frontend → http://localhost:3000
```

> 首次接手 / 收口 verify 清单见 [`docs/handoff.md`](docs/handoff.md)。

## 子项目

| 路径 | 说明 |
|---|---|
| `backend/` | FastAPI 后端 + ingestion + processing + scheduler |
| `frontend/` | Next.js Web 应用 |
| `cli/` | `hub` 命令行(本地投喂 / 检索) |
| `docker/` | docker-compose 编排 |
| `openspec/` | 升级规划与逐 change 任务 |
| `backend/legacy/` | 旧 ai-news-agent 代码,迁移期保留 |

## 开发

- 后端:`cd backend && uv sync && uv run uvicorn app.main:app --reload`
- 前端:`cd frontend && pnpm install && pnpm dev`
- CLI:`cd cli && pipx install -e .`,然后 `hub --version`

## 升级历史

旧 `ai-news-agent` README 与邮件/Telegram 文档已下线;迁移说明见 [`docs/migration-from-v1.md`](docs/migration-from-v1.md)(由 013 change 提供)。
